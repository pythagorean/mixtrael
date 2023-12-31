import panel as pn
from claude_api import Client as ClaudeClient
from hugchat import hugchat
from claude import get_claude_client
from mixtral import hugchat_model, get_hugchat_client

pn.extension(design="material")


def get_claude_conversations(claude):
    return [(conv['uuid'], conv['name']) for conv in reversed(claude.list_all_conversations())]


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


def create_client_selection_config(i):
    return pn.widgets.Select(name=f'Client {i}', options=['Echo', 'Mixtral', 'Claude'])


number_of_conversations = pn.widgets.IntSlider(
    name='Number of conversations', value=2, start=2, end=8)
configure_button = pn.widgets.Button(name="Configure")


start_panel = pn.Column(
    number_of_conversations,
    configure_button
)


def configure_client_panel(client_type, clients):
    if clients.count(client_type) > 1:
        raise ValueError(
            f'Only one {client_type} client can currently be selected')
    client = get_hugchat_client() if client_type == 'Mixtral' else get_claude_client()
    conversations = get_mixtral_conversations(
        client) if client_type == 'Mixtral' else get_claude_conversations(client)

    conversation_options = {'0. Start a new conversation': 'New'}
    conversation_dict = {}
    for i, (conv_id, title) in enumerate(conversations, 1):
        conv_id_str = str(conv_id)
        conversation_dict[conv_id_str] = conv_id
        conversation_options[f"{i}. {title}"] = conv_id_str

    return pn.widgets.Select(
        options=conversation_options,
        value=None,
        name=f"Select a {client_type} conversation"
    ), conversation_dict


def create_configuration_panel_elements(clients, selected_conversations):
    configuration_panel_elements = []
    for i, client in enumerate(clients):
        if client == 'Echo':
            continue
        select_info = selected_conversations[client]
        configuration_panel_elements.extend(
            [f"Conversation {i+1}", select_info['select']])
    return configuration_panel_elements


def configure_panel(event, selected_conversations, app):
    app.clear()
    for client_type, select_info in selected_conversations.items():
        selected_conversation = select_info['select'].value
        if selected_conversation == 'New':
            if client_type == 'Claude':
                new_chat = get_claude_client().create_new_chat()
                current_conversation = new_chat['uuid']
            elif client_type == 'Mixtral':
                get_hugchat_client().new_conversation(switch_to=True)
        else:
            current_conversation = select_info['dict'][selected_conversation]

        if client_type == 'Claude':
            chat = get_chat_interface(lambda contents, user, instance: anthropic_callback(
                contents, user, instance, get_claude_client(), current_conversation), placeholder="Text to Claude!")
        elif client_type == 'Mixtral':
            chat = get_chat_interface(lambda contents, user, instance: hugchat_callback(
                contents, user, instance, get_hugchat_client()), placeholder="Text to Mixtral!")

        app.append(chat)


def configured_start_panel(event, number_of_conversations, configure_button, start_panel, app):
    num_conversations = number_of_conversations.value
    client_selection_configs = [create_client_selection_config(
        i) for i in range(1, num_conversations + 1)]
    select_clients_panel = pn.Column(
        *client_selection_configs, configure_button)

    def selected_clients_panel(event):
        app.clear()
        clients = [client.value for client in client_selection_configs]
        selected_conversations = {}

        for client_type in clients:
            if client_type == 'Echo':
                continue

            select_conversation, conversation_dict = configure_client_panel(
                client_type, clients)
            selected_conversations[client_type] = {
                'select': select_conversation, 'dict': conversation_dict}

        configuration_panel_elements = create_configuration_panel_elements(
            clients, selected_conversations)
        configuration_panel = pn.Column(
            *configuration_panel_elements, configure_button)

        pn.bind(lambda event: configure_panel(
            event, selected_conversations, app), configure_button, watch=True)
        app.append(configuration_panel)

    app.clear()
    pn.bind(selected_clients_panel, configure_button, watch=True)
    app.append(select_clients_panel)


app = start_panel
pn.bind(lambda event: configured_start_panel(
    event, number_of_conversations, configure_button, start_panel, app), configure_button, watch=True)
app.servable()
