import torch
import torch.nn as nn
from torch.nn import functional as F
import mmap
import pickle

device = "cuda" if torch.cuda.is_available() else "cpu"
batch_size = 64
block_size = 128
max_iters = 200
learning_rate = 3e-4
eval_iters = 100
n_embd = 384
n_head = 8
n_layer = 8
dropout = 0.2 # 20% of neurons are dropped out from network
print(device)

chars = ""
with open('train/vocab.txt', 'r', encoding = 'utf-8') as f:
    text = f.read()
    chars = sorted(list(set(text)))
vocab_size = len(chars)

#tokenizer
string_to_int = {ch:i for i,ch in enumerate(chars)}
int_to_string = {i:ch for i,ch in enumerate(chars)}
encode= lambda s: [string_to_int[c]for c in s]
decode= lambda l: ''.join([int_to_string[i] for i in l])

import random as random
def get_random_chunk(split):
    filename = 'train/train_split.txt' if split == 'train' else 'train/val_split.txt'
    with open(filename, 'rb') as f:
        with mmap.mmap(f.fileno(), 0, access =mmap.ACCESS_READ) as mm:

            file_size = len(mm)
            start_pos = random.randint(0, (file_size) - block_size * batch_size)
            mm.seek(start_pos)
            block = mm.read(block_size * batch_size -1 )

            decoded_block = block.decode('utf-8', errors='ignore').replace('\r', '')

            data = torch.tensor(encode(decoded_block), dtype = torch.long)
            
    return data

def get_batch(split):
    data = get_random_chunk(split)
    ix = torch.randint(len(data) - block_size, (batch_size,))
    x = torch.stack([data[i:i+block_size] for i in ix])
    y = torch.stack([data[i+1:i+block_size+1] for i in ix])
    x,y = x.to(device), y.to(device)
    return x,y

@torch.no_grad()
def estimate_loss():
    out = {}
    model.eval()
    for split in ['train','val']:
        losses = torch.zeros(eval_iters)
        for k in range (eval_iters):
            x,y = get_batch(split)
            logits, loss = model(x, y)
            losses[k] = loss.item()
        out[split] = losses.mean()
    model.train()
    return out

class Head(nn.Module):

    """ One head of self-attention """
    def __init__(self, head_size):
         super().__init__()
         self.key = nn.Linear(n_embd, head_size, bias = False)
         self.query = nn.Linear(n_embd, head_size, bias = False)
         self.value = nn.Linear(n_embd, head_size, bias = False)
         self.register_buffer ('tril', torch.tril(torch.ones(block_size, block_size)))

         self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        # input of size (batch, time-step, channels)
        # output of size (batch, time-step, head size)
        B,T,C = x.shape
        k = self.key(x) # (B, T, hs)
        q = self.query(x) # (B, T, hs)

        # compute attention scores ("affinities")
        wei = q @ k.transpose(-2,-1) * k.shape[-1]**-0.5 # q = (B, T, hs) @ k = (B, hs, T)[they are flip because of transpose (-2,-1)] --> (B, T, T)
        # k.shape[-1] ** -0.5 = scaling by 1/sqrt(length of rows in key or quaries matrix or dk)
        wei = wei.masked_fill(self.tril[:T, :T] == 0, float('-inf')) # (B, T, T)
        wei = F.softmax(wei, dim =-1) # (B, T, T)
        wei = self.dropout(wei)

        # perform the weight aggregration of the values
        v = self.value(x) # (B, T, hs)
        out = wei @ v # (B, T, hs) @ (B, hs, T) --> (B, T, T)
        return out
        
class MultiHeadAttention(nn.Module):

    """ Multiple heads of self-attention in parallel """
    def __init__(self, num_heads, head_size):
        super().__init__() 
        self.heads = nn.ModuleList([Head(head_size) for _ in range (num_heads)])
        self.proj = nn.Linear (head_size * num_heads, n_embd)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        out = torch.cat([h(x) for h in self.heads], dim =-1 )
        out = self.dropout(self.proj(out))
        return out

class FeedForward(nn.Module):
    
    """ A simple linear layer followed by a non-linearity"""
    def __init__(self, n_embd):
        super().__init__()
        # Linear --> ReLU --> Linear
        self.net = nn.Sequential(
            nn.Linear(n_embd, 4 * n_embd),
            nn.ReLU(),
            nn.Linear(4 * n_embd, n_embd),
            nn.Dropout(dropout) # Used to prevent overfitting
        )

    def forward(self, x):
        return self.net(x)

class Block(nn.Module):
    
    """ Transformer block: Communication followed by computing """
    def __init__(self, n_embd, n_head):
        super().__init__()
        head_size = n_embd
        self.sa = MultiHeadAttention(n_head, head_size)
        self.fdwd = FeedForward(n_embd)  # Linear --> ReLU --> Linear
        self.ln1 = nn.LayerNorm(n_embd)
        self.ln2 = nn.LayerNorm(n_embd)

        # The below forward goes this way: Self_attention --> add & norm --> Feed Forward --> add & norm
    def forward(self, x):
        y = self.sa(x) 
        x = self.ln1(x + y)
        y = self.fdwd(x)
        x = self.ln2(x + y)
        return x

class GPTLanguageModel(nn.Module):
    def __init__(self, vocab_size):
        super().__init__()
        # nn.Embedding: This is used to convert token indices into dense vectors. 
        self.token_embedding_table = nn.Embedding(vocab_size, n_embd)
        self.position_embedding_table = nn.Embedding(block_size,n_embd)
        # The code below is for how many decoder blocks we are running sequentially.
        # Have to change after some time or develop our model, maximum is 6
        self.blocks = nn.Sequential (*[Block(n_embd, n_head = n_head) for _ in range (n_layer)])

        self.ln_f = nn.LayerNorm(n_embd) #final layer norm
        self.lm_head = nn.Linear(n_embd, vocab_size)

        self.apply(self._init_weights)

    def _init_weights(self,module):
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean = 0.0, std = 0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
            elif isinstance(module, nn.Embedding):
                torch.n.init.normal_(module.weight, mean = 0.0, std = 0.02)

    def forward(self, index, targets=None):
        B, T = index.shape

        # index and targets are both (B, T) tensors of integers
        tok_emb= self.token_embedding_table(index) # (B, T, C)
        pos_emb= self.position_embedding_table(torch.arange(T, device = device)) # (T, C)
        x = tok_emb + pos_emb # (B, T, C)
        x = self.blocks(x) # (B, T, C)
        x = self.ln_f(x) # (B, T, C)
        logits = self.lm_head(x) # (B, T, vocab_size)
        
        if targets is None:
            loss = None
        else:
            # B= Block, T= Time step, C = Channels
            B, T, C = logits.shape
            logits = logits.view(B*T,C)
            targets = targets.view(B*T)
            # F.cross_entropy: This computes the cross-entropy loss between the model's predictions (logits) and the true targets
            #  It trains the model by minimizing this loss.
            loss = F.cross_entropy(logits,targets)
        return logits, loss

    def generate(self, index, max_new_tokens):
        for _ in range(max_new_tokens):
            #get the predictions
            logits, loss = self.forward(index)
            #focus only on the last time step
            logits = logits [:, -1, :]
            # F.softmax: This converts the logits into probabilities, which are used to sample the next token during text generation.
            probs = F.softmax(logits, dim =-1)
            # torch.multinomial: This samples the next token based on the computed probabilities, introducing randomness in the generation process.
            index_next = torch.multinomial (probs, num_samples = 1)
            # torch.cat: This concatenates the newly generated token with the existing sequence, allowing the model to generate text iteratively.
            index = torch.cat((index, index_next), dim = 1)
        return index

model = GPTLanguageModel(vocab_size)
print('loading model....')
with open('model-01.pkl', 'rb') as f:
    model = pickle.load(f)
print('loded succcessful!')
m = model.to(device)


optimizer = torch.optim.AdamW(model.parameters(), lr = learning_rate)
for iter in range (max_iters):
    if iter % eval_iters == 0:
        losses = estimate_loss()
        print(f"Step {iter}: Train Loss {losses['train']:.4f}, Val Loss: {losses['val']:.4f}")

    # sample a batch of data
    xb, yb = get_batch('train')

    #evaluate the loss
    logits, loss = model.forward(xb,yb)
    optimizer.zero_grad(set_to_none =True)
    loss.backward()
    optimizer.step()
print(loss.item())

with open('model-01.pkl','wb') as f:
    pickle.dump(model,f)
print('model saved')