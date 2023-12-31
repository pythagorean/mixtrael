import panel as pn
from claude_api import Client as ClaudeClient
from hugchat import hugchat
from claude import get_claude_client
from mixtral import hugchat_model, get_hugchat_client

pn.extension(design="material")


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


number_of_conversations = pn.widgets.IntSlider(
    name='Number of conversations', value=2, start=2, end=8)

configure_button = pn.widgets.Button(name="Configure")


start_panel = pn.Column(
    number_of_conversations,
    configure_button
)


def create_client_selection_config(i):
    client = pn.widgets.Select(name=f'Client {i}', options=[
                               'Echo', 'Mixtral', 'Claude'])
    return client


def configured_start_panel(event):
    num_conversations = number_of_conversations.value
    client_selection_configs = [create_client_selection_config(
        i) for i in range(1, num_conversations+1)]
    select_clients_panel = pn.Column(
        *client_selection_configs,
        configure_button
    )

    def selected_clients_panel(event):
        app.clear()
        clients = [client.value for client in client_selection_configs]
        if 'Claude' in clients:
            if clients.count('Claude') > 1:
                raise ValueError(
                    'Only one Claude client can currently be selected')
            anthropic_claude = get_claude_client()
            claude_conversations = get_claude_conversations(anthropic_claude)
            anthropic_claude_current_conversation = None
            claude_conversation_selections = {
                '0. Start a new conversation': 'New'}
            for i, (conv_id, title) in enumerate(claude_conversations, 1):
                claude_conversation_selections[f"{i}. {title}"] = conv_id
            select_claude_conversation = pn.widgets.Select(
                options=claude_conversation_selections,
                value=None,
                name="Select a conversation"
            )
        if 'Mixtral' in clients:
            if clients.count('Mixtral') > 1:
                raise ValueError(
                    'Only one Mixtral client can currently be selected')
            hugchat_mixtral = get_hugchat_client()
            mixtral_conversations = get_mixtral_conversations(hugchat_mixtral)
            hugchat_mixtral.current_conversation = None
            mixtral_conversation_selections = {
                '0. Start a new conversation': 'New'}
            mixtral_conversation_dict = {}
            for i, (conv_id, title) in enumerate(mixtral_conversations, 1):
                conv_id_str = str(conv_id)
                mixtral_conversation_dict[conv_id_str] = conv_id
                mixtral_conversation_selections[f"{i}. {title}"] = conv_id_str
            select_mixtral_conversation = pn.widgets.Select(
                options=mixtral_conversation_selections,
                value=None,
                name="Select a conversation"
            )

        configuration_panel_elements = []
        for i, client in enumerate(clients):
            if client == 'Claude':
                configuration_panel_elements.append(
                    f"Claude Conversation {i+1}")
                configuration_panel_elements.append(select_claude_conversation)
            elif client == 'Mixtral':
                configuration_panel_elements.append(
                    f"Mixtral Conversation {i+1}")
                configuration_panel_elements.append(
                    select_mixtral_conversation)

        configuration_panel = pn.Column(
            *configuration_panel_elements,
            configure_button
        )

        def configured_panel(event):
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

            echo_chat = get_chat_interface(
                echo_callback, placeholder="Text to echo")

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

        pn.bind(configured_panel, configure_button, watch=True)
        app.append(configuration_panel)

    app.clear()
    pn.bind(selected_clients_panel, configure_button, watch=True)
    app.append(select_clients_panel)


pn.bind(configured_start_panel, configure_button, watch=True)
app = start_panel


app.servable()
