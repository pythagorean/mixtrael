import os
import panel as pn
from hugchat import hugchat
from hugchat.login import Login

hugchat_cookie_path = './.cookies/hugchat'
hugchat_model = "mistralai/Mixtral-8x7B-Instruct-v0.1"


def hugchat_login() -> hugchat.RequestsCookieJar:
    cookie_list = os.listdir(hugchat_cookie_path)
    cookie_files = [
        cookies for cookies in cookie_list if cookies.endswith('.json')]
    if len(cookie_files) != 1:
        print("There should be a single json file in the hugchat cookie path")
        exit(1)
    name = cookie_files[0][:-5]
    sign = Login(name, None)
    cookies = sign.loadCookiesFromDir(hugchat_cookie_path)
    return cookies


def get_hugchat_model() -> hugchat.ChatBot:
    cookies = hugchat_login()
    chatbot = hugchat.ChatBot(cookies=cookies.get_dict())
    chatbot.delete_conversation()
    chatbot.get_remote_conversations(replace_conversation_list=True)
    models = chatbot.get_available_llm_models()
    for model_num in range(0, len(models)):
        model = str(models[model_num])
        if model == hugchat_model:
            chatbot.switch_llm(model_num)
            return chatbot
    print(f"Hugchat model '{hugchat_model}' not found")
    exit(1)


hugchat = get_hugchat_model()
hugchat_list = hugchat.get_conversation_list()

for id in hugchat_list:
    hugchat.change_conversation(id)
    info = hugchat.get_conversation_info()
    print(info.id, info.title, info.model)

pn.extension(design="material")


async def callback(contents: str, user: str, instance: pn.chat.ChatInterface):
    message = f"Echoing {user}: {contents}"
    return message


def get_chat_interface() -> pn.chat.ChatInterface:
    chat_interface = pn.chat.ChatInterface(
        callback=callback,
        widgets=pn.widgets.TextAreaInput(
            placeholder="Text to echo",
            auto_grow=True,
            rows=1),
        show_rerun=False,
        show_undo=False,
        show_clear=False)
    return chat_interface


pn.Column(
    get_chat_interface(),
    pn.widgets.TextAreaInput(
        placeholder="Buffer space",
        auto_grow=True,
        rows=1),
    get_chat_interface(),
).servable()
