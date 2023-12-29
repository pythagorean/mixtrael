import panel as pn
from claude_api import Client as ClaudeClient
from hugchat import hugchat
from claude import get_claude_client
from mixtral import hugchat_model, get_hugchat_client

pn.extension(design="material")
anthropic_claude = get_claude_client()
hugchat_mixtral = get_hugchat_client()


def get_claude_conversations(claude):
    conversations = []
    for conversation in claude.list_all_conversations():
        conversations.append((conversation['uuid'], conversation['name']))
    return reversed(conversations)


def get_mixtral_conversations(mixtral):
    conversations = []
    for conv_id in mixtral.get_conversation_list():
        mixtral.change_conversation(conv_id)
        conversation = mixtral.get_conversation_info()
        if conversation.model == hugchat_model:
            conversations.append((conv_id, str(conversation.title)))
    return conversations


async def echo_callback(contents: str, user: str, instance: pn.chat.ChatInterface) -> str:
    return f"Echoing {user}: {contents}"


async def anthropic_callback(contents: str, user: str, instance: pn.chat.ChatInterface, client: ClaudeClient, conversation_uuid: str) -> str:
    query_result = client.send_message(contents, conversation_uuid)
    return str(query_result)


async def hugchat_callback(contents: str, user: str, instance: pn.chat.ChatInterface, client: hugchat.ChatBot) -> str:
    query_result = client.query(contents)
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


claude_conversations = get_claude_conversations(anthropic_claude)
anthropic_claude_current_conversation = None
mixtral_conversations = get_mixtral_conversations(hugchat_mixtral)
hugchat_mixtral.current_conversation = None

claude_conversation_selections = {'0. Start a new conversation': 'New'}
for i, (conv_id, title) in enumerate(claude_conversations, 1):
    claude_conversation_selections[f"{i}. {title}"] = conv_id

mixtral_conversation_selections = {'0. Start a new conversation': 'New'}
mixtral_conversation_dict = {}
for i, (conv_id, title) in enumerate(mixtral_conversations, 1):
    conv_id_str = str(conv_id)
    mixtral_conversation_dict[conv_id_str] = conv_id
    mixtral_conversation_selections[f"{i}. {title}"] = conv_id_str

select_claude_conversation = pn.widgets.Select(
    options=claude_conversation_selections,
    value=None,
    name="Select a conversation"
)

select_mixtral_conversation = pn.widgets.Select(
    options=mixtral_conversation_selections,
    value=None,
    name="Select a conversation"
)

configure_button = pn.widgets.Button(name="Configure")

configuration_panel = pn.Column(
    "Select Claude Conversation",
    select_claude_conversation,
    "Select Mixtral Conversation",
    select_mixtral_conversation,
    configure_button
)

app = configuration_panel


def configure_app(event):
    selected_claude_conversation = select_claude_conversation.value
    if selected_claude_conversation == 'New':
        new_chat = anthropic_claude.create_new_chat()
        anthropic_claude_current_conversation = new_chat['uuid']
    else:
        anthropic_claude_current_conversation = selected_claude_conversation

    selected_mixtral_conversation = select_mixtral_conversation.value
    if selected_mixtral_conversation == 'New':
        hugchat_mixtral.new_conversation(switch_to=True)
    else:
        hugchat_mixtral.change_conversation(
            mixtral_conversation_dict[selected_mixtral_conversation])

    mixtral_conversation = hugchat_mixtral.get_conversation_info()
    mixtral_conversation_title = pn.pane.Markdown(
        f"# Current Conversation: {mixtral_conversation.title}")

    echo_chat = get_chat_interface(echo_callback, placeholder="Text to echo")

    claude_chat = get_chat_interface(
        lambda contents, user, instance: anthropic_callback(
            contents, user, instance, anthropic_claude, anthropic_claude_current_conversation),
        placeholder="Text to Claude!")

    mixtral_chat = get_chat_interface(
        lambda contents, user, instance: hugchat_callback(
            contents, user, instance, hugchat_mixtral),
        placeholder="Text to Mixtral!")

    buffer = pn.widgets.TextAreaInput(
        placeholder="Buffer space", auto_grow=True, rows=1)
    copy_button = pn.widgets.Button(name='Copy to Buffer')
    paste_button = pn.widgets.Button(name='Paste to Echo')
    buffer_space = pn.Row(
        buffer,
        copy_button,
        paste_button
    )

    main_panel = pn.Column(
        claude_chat,
        buffer_space,
        mixtral_conversation_title,
        mixtral_chat
    )

    app.clear()
    app.append(main_panel)


pn.bind(configure_app, configure_button, watch=True)

app.servable()
