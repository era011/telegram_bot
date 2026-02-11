import openai
import os




def classification(message: str, chunk: dict) -> str:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """Ты классифицируешь вопросы, следующим образом:
If message не является вопросом, 
    то просто выводишь 'Нет'
Elif в chunk есть ответ на вопрос message,
    то просто выводишь 'Да'
Else,
    то просто выводишь 'Нет'

Пример:
message-'как начислить кофе?'
chunk-'content': 'name Начисление кофе ИБТС...'
Вывод-'Да'

message-'как меня зовут?'
chunk-'...'
Вывод-'Нет'
"""
            },
            {
                "role": "user",
                "content": f"message-'{message}'\nchunk-'content': '{chunk}'"
            }
        ]
    )
    
    return response.choices[0].message.content.strip()                
    