from datetime import datetime

from langchain_core.prompts import PromptTemplate, ChatPromptTemplate,MessagesPlaceholder, SystemMessagePromptTemplate, HumanMessagePromptTemplate, AIMessagePromptTemplate

# prompt = PromptTemplate.from_template("请讲一个{subject}笑话")
# print(prompt.format(subject="程序员"))
# prompt = prompt.invoke({"subject": "程序员"})
# print(prompt.to_messages())
# print(prompt.to_messages()[0].content)

chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个有十年python工作经验的程序员，请根据用户的需求，提供专业的建议,当前时间为{time}"),
    MessagesPlaceholder("chat_history"),
    HumanMessagePromptTemplate.from_template("请讲一个{subject}笑话")
]).partial(time=datetime.now())

print(chat_prompt.invoke({
    "chat_history": [
        HumanMessagePromptTemplate.from_template("你是谁？").format(),
        AIMessagePromptTemplate.from_template("我是一个有十年python工作经验的程序员").format()
    ],
    "subject": "程序员"
}))