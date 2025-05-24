import pandas as pd
import torch
import torch.nn.functional as F
import json

from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel


class RecommenderService:

    _TASK = "Find similar wine descriptions"

    def __init__(self):
        raw_data = pd.read_csv("wines_new.csv")
        wine_columns = list(raw_data.columns)
        df = raw_data[wine_columns][raw_data['Тип продукта']!='Оливковое масло'].copy()
        desc_col = wine_columns[2:]
        for col in desc_col:
            df[col] = df[col].astype(str).fillna("")
            
        df['Описание вина'] = df.apply(lambda row: ". ".join([f"{col} - {row[col]}"
                                                      for col in desc_col]), axis=1)
        self._df = df
        self._texts = df["Описание вина"].tolist()

        self._tokenizer = AutoTokenizer.from_pretrained('intfloat/multilingual-e5-large-instruct')
        self._model = AutoModel.from_pretrained('intfloat/multilingual-e5-large-instruct')

        self._wine_vectors = torch.load('wine_vectors.pt')

    def recommend(self, query: str, mode: str) -> str:
        user_query = query
        formatted_query = self.get_detailed_instruct(self._TASK, user_query)

        # Tokenize the user query
        query_inputs = self._tokenizer(formatted_query, max_length=512,
                                padding=True, truncation=True, return_tensors='pt')

        # Generate embeddings for the query
        with torch.no_grad():
            query_outputs = self._model(**query_inputs)

        # Pool and normalize the query embeddings
        query_embeddings = self.average_pool(query_outputs.last_hidden_state,
                                        query_inputs['attention_mask'])
        query_vector = F.normalize(query_embeddings, p=2, dim=1).squeeze()

        # Calculate similarities (assuming wine_vectors are already normalized)
        similarities = torch.matmul(query_vector, torch.stack(self._wine_vectors).T)

        # Find top-N similar wines
        top_n = 5
        top_indices = torch.topk(similarities, top_n).indices.tolist()

        # Extract matching wines
        best_wines = self._df.iloc[top_indices].to_json(orient='records', force_ascii=False)

        best_wines = json.loads(best_wines)

        return best_wines

    def average_pool(self, last_hidden_states: torch.Tensor,
                 attention_mask: torch.Tensor) -> torch.Tensor:
        last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
        return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]

    def get_detailed_instruct(self, task_description: str, query: str) -> str:
        return f'Instruct: {task_description}\nQuery: {query}'
