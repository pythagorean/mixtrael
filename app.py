import panel as pn
from hugchat import hugchat
from mixtral import hugchat_model, get_hugchat_chatbot

pn.extension(design="material")
hugchat_mixtral = get_hugchat_chatbot()


def get_mixtral_conversations(chatbot):
    conversations = []
    for conv_id in chatbot.get_conversation_list():
        chatbot.change_conversation(conv_id)
        conversation = chatbot.get_conversation_info()
        if conversation.model == hugchat_model:
            conversations.append((conv_id, str(conversation.title)))
    return conversations


async def echo_callback(contents: str, user: str, instance: pn.chat.ChatInterface) -> str:
    return f"Echoing {user}: {contents}"


async def hugchat_callback(contents: str, user: str, instance: pn.chat.ChatInterface, chatbot: hugchat.ChatBot) -> str:
    query_result = chatbot.query(contents)
    return str(query_result)


def get_chat_interface(callback, placeholder) -> pn.chat.ChatInterface:
    return pn.chat.ChatInterface(
        callback=callback,
        widgets=pn.widgets.TextAreaInput(
            placeholder=placeholder,
            auto_grow=True,
            rows=1),
        show_rerun=False,
        show_undo=False,
        show_clear=False
    )


main_panel = pn.Column(
    get_chat_interface(echo_callback, placeholder="Text to echo"),
    pn.widgets.TextAreaInput(
        placeholder="Buffer space", auto_grow=True, rows=1),
    get_chat_interface(lambda contents, user, instance: hugchat_callback(contents, user, instance, hugchat_mixtral),
                       placeholder="Text to Mixtral!")
)

mixtral_conversations = get_mixtral_conversations(hugchat_mixtral)
hugchat_mixtral.current_conversation = None

conversation_selections = {'0. Start a new conversation': 'New'}
conversation_dict = {}
for i, (conv_id, title) in enumerate(mixtral_conversations, 1):
    conv_id_str = str(conv_id)
    conversation_dict[conv_id_str] = conv_id
    conversation_selections[f"{i}. {title}"] = conv_id_str


def configure_app(event):
    selected_conversation = select_conversation.value
    if selected_conversation == 'New':
        hugchat_mixtral.new_conversation(switch_to=True)
    else:
        hugchat_mixtral.change_conversation(
            conversation_dict[selected_conversation])


select_conversation = pn.widgets.Select(
    options=conversation_selections,
    value=None,
    name="Select a conversation"
)

configure_button = pn.widgets.Button(name="Configure")

configuration_panel = pn.Column(
    select_conversation,
    configure_button
)


app = pn.Tabs(
    ("Configuration", configuration_panel),
    ("Main Screen", main_panel),
)


pn.bind(configure_app, configure_button, watch=True)

app.servable()
