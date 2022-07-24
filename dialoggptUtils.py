from transformers import AutoModelForCausalLM, AutoTokenizer
import torch


def load_tokenizer_and_model(model="microsoft/DialoGPT-large"):
  """
    Load tokenizer and model instance for some specific DialoGPT model.
  """
  # Initialize tokenizer and model
  print("Loading model...")
  tokenizer = AutoTokenizer.from_pretrained(model)
  model = AutoModelForCausalLM.from_pretrained(model)
  
  # Return tokenizer and model
  return tokenizer, model


def generate_response(tokenizer, model, newChat, chat_history_ids,user_input):
  """
    Generate a response to some user input.
  """
  # Encode user input and End-of-String (EOS) token
  new_input_ids = tokenizer.encode(user_input + tokenizer.eos_token, return_tensors='pt')

  # Append tokens to chat history
  bot_input_ids = torch.cat([chat_history_ids, new_input_ids], dim=-1) if not newChat > 0 else new_input_ids

  # Generate response given maximum chat length history of 1250 tokens
  chat_history_ids = model.generate(bot_input_ids, do_sample=True, 
        max_length=1000,
        top_k=50, 
        top_p=0.95, pad_token_id=tokenizer.eos_token_id, temperature=0.8)
  
  # Print response
  response=tokenizer.decode(chat_history_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True)
  
  # Return the chat history ids
  return chat_history_ids,response
