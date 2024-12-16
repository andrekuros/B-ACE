import torch
import torch.nn as nn
import numpy as np

class Task_MHA_B_ACE(nn.Module):
    def __init__(
        self,
        num_tasks: int = 10,
        num_features_per_task: int = 8,
        device: str = "cpu",
        nhead: int = 4,
    ):
        super().__init__()

        self.device = device
        self.num_tasks = num_tasks  # Number of max tasks (e.g., 20)
        self.embedding_size = 256  # Customizable

        # Task encoder: Fully connected layers
        # Each task has num_features_per_task feature      

        self.task_encoder = nn.Sequential(
            nn.Linear(num_features_per_task, 32),
            nn.ReLU(),
            nn.Linear(32, 64),
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.Linear(128, 256),
            nn.ReLU(),
            #nn.Linear(256, 512),
            #nn.ReLU(),
            nn.Linear(256, self.embedding_size)  # Ensure this matches the action space
        ).to(device)

        # Multi-head attention layers
        self.own_attention = nn.MultiheadAttention(embed_dim=self.embedding_size, num_heads=nhead, batch_first=True).to(device)
        self.norm1 = nn.LayerNorm(self.embedding_size).to(device)
        self.own_attention2 = nn.MultiheadAttention(embed_dim=self.embedding_size, num_heads=nhead, batch_first=True).to(device)       


        # self.output = nn.Sequential(
        #     nn.Linear(self.embedding_size, 256),
        #     nn.ReLU(),
        #     nn.Linear(256, 128),
        #     nn.ReLU(),          
        #     nn.Linear(128, 64),
        #     nn.ReLU(),          
        #     nn.Linear(64, 1)  # Ensure this matches the action space

        # ).to(device)

        self.output = nn.Sequential(
            nn.Linear(self.embedding_size, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),          
            nn.Linear(128, 64),
            nn.ReLU(),          
            nn.Linear(64, 1)  # Ensure this matches the action space

        ).to(device)
      

    def forward(self, obs, state=None, info=None):
        # obs shape is expected to be [batch_size, num_tasks, num_features_per_task]
                
        
        #print("MHA", [obs, info])
        if isinstance(obs, np.ndarray):
            observation = torch.tensor(np.array(obs), dtype=torch.float32).to(self.device)            
            mask = info.mask
        else:            
            observation = torch.tensor(np.array(obs[info].obs), dtype=torch.float32).to(self.device)
            mask =  obs[info].mask
                    
        
        mask = ~mask #for pythorch
        mask = torch.tensor(mask, dtype=torch.bool).to(self.device)
        # Process each task independently through the task encoder
        batch_size, num_tasks, num_features = observation.shape                
        
        obs_reshaped = observation.view(-1, num_features)  # [batch_size * num_tasks, num_features]
        task_embeddings = self.task_encoder(obs_reshaped)  # [batch_size * num_tasks, embedding_size]
        task_embeddings = task_embeddings.view(batch_size, num_tasks, -1)  # Reshape back to [batch_size, num_tasks, embedding_size]      

        # Attention mechanism
        attention_output1, _ = self.own_attention(task_embeddings, task_embeddings, task_embeddings, key_padding_mask = mask)                
        attention_output1 = attention_output1 + task_embeddings        
        attention_output1 = self.norm1(attention_output1)
        
        # mask_expanded = mask.unsqueeze(-1).expand_as(attention_output1)               
        # attention_output1 = attention_output1.masked_fill(mask_expanded, 0.0)

        attention_output2, _ = self.own_attention2(attention_output1, attention_output1, attention_output1, key_padding_mask=mask)               
        attention_output2 = attention_output2 + attention_output1        
        # attention_output2 = self.norm2(attention_output2)
        # attention_output2 = attention_output2.masked_fill(mask_expanded, 0.0)       

        #task_q_values = self.output(attention_output1)                   
        task_q_values = self.output(attention_output2)                   
        task_q_values = torch.squeeze(task_q_values, -1).to(self.device)           

        return task_q_values, state
