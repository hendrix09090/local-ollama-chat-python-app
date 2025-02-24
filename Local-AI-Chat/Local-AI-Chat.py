import flet as ft
import requests
import json
import threading
import datetime
import webbrowser
import os
import time

class ChatApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Local AI Chat"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 20
        self.ollama_url = "http://localhost:11434/api/generate"
        self.models_url = "http://localhost:11434/api/tags"
        
        # State management
        self.current_model = ft.Ref[ft.Dropdown]()
        self.user_name = ft.Ref[str]()
        self.ai_thinking_message = ft.Ref[str]()
        self.chat_sessions = ft.Ref[list]()
        self.current_chat_id = ft.Ref[int]()
        self.selected_chat_id = ft.Ref[int]()
        self.ai_message = None  # To track the current AI message control

        # Initialize ref values
        self.user_name.value = "Danny"
        self.ai_thinking_message.value = "🤔 Ai Ron is thinking..."
        self.chat_sessions.value = []
        self.current_chat_id.value = None

        # Load chat history
        self.load_chat_history()

        # Build UI
        self.build_ui()
        self.load_models()

        # Update chat list to reflect loaded sessions
        self.update_chat_list()

    def build_ui(self):
        """Build the main UI layout"""
        # Model selection dropdown
        self.model_dropdown = ft.Dropdown(
            ref=self.current_model,
            hint_text="Select Model",
            on_change=self.handle_model_change,
            options=[],
            expand=True,
            width=300,  # Set fixed width
            autofocus=True,
            label="AI Model",
            hint_style=ft.TextStyle(color=ft.Colors.GREY_400)
        )

        # Chat history sidebar
        self.chat_list = ft.ListView(expand=True, spacing=5)
        self.sidebar = ft.Column(
            controls=[
                ft.Text("Chat History", size=18, weight=ft.FontWeight.BOLD),
                ft.ElevatedButton("New Chat", on_click=self.handle_new_chat),
                ft.Divider(),
                self.model_dropdown,
                ft.Divider(),
                self.chat_list
            ],
            width=300,  # Increased from 200
            spacing=10
        )

        # Main chat area
        self.chat_input = ft.TextField(
            hint_text="Type your message...",
            expand=True,
            on_submit=self.handle_send_message
        )
        self.chat_history = ft.ListView(expand=True, auto_scroll=True)
        
        # Assemble main layout
        self.page.add(
            ft.Row(
                controls=[
                    self.sidebar,
                    ft.VerticalDivider(width=1),
                    ft.Column(
                        controls=[
                            self.chat_history,
                            ft.Row(
                                controls=[
                                    self.chat_input,
                                    ft.ElevatedButton("Send", on_click=self.handle_send_message),
                                    ft.ElevatedButton("Clear Chat", on_click=self.handle_clear_chat)
                                ],
                                alignment=ft.MainAxisAlignment.END
                            )
                        ],
                        expand=True
                    )
                ],
                expand=True
            )
        )

    # -- Model Management --
    def load_models(self):
        """Load available models from Ollama"""
        try:
            # First check if Ollama is running
            ping_response = requests.get("http://localhost:11434")
            if ping_response.status_code != 200:
                self.show_error("Ollama not running! Start Ollama first.", ft.Colors.RED)
                return
            
            response = requests.get(self.models_url)
            if response.status_code == 200:
                models = response.json().get('models', [])
                self.current_model.current.options = [
                    ft.dropdown.Option(model['name']) for model in models
                ]
                if models:
                    self.current_model.current.value = models[0]['name']
                self.page.update()
        except requests.ConnectionError:
            self.show_error("Cannot connect to Ollama. Make sure it's running!", ft.Colors.RED)

    def handle_model_change(self, e):
        """Handle model selection change"""
        if self.current_model.current.value:
            self.show_error(f"Model changed to: {self.current_model.current.value}", color=ft.Colors.BLUE)

    # -- Chat Sessions --
    def handle_new_chat(self, e):
        """Create a new chat session"""
        new_chat = {
            "id": len(self.chat_sessions.value) + 1,
            "name": f"Chat {len(self.chat_sessions.value) + 1}",
            "messages": [],
            "created_at": datetime.datetime.now().isoformat()
        }
        self.chat_sessions.value.append(new_chat)
        self.current_chat_id.value = new_chat["id"]
        self.update_chat_list()
        self.handle_clear_chat(e)
        self.save_chat_history()  # Save chat history after creating a new chat

    def update_chat_list(self):
        """Update the sidebar chat list"""
        self.chat_list.controls.clear()
        for chat in self.chat_sessions.value:
            self.chat_list.controls.append(
                ft.ListTile(
                    title=ft.Text(chat["name"]),
                    on_click=lambda e, cid=chat["id"]: self.load_chat(cid),
                    trailing=ft.IconButton(
                        icon=ft.icons.DELETE,
                        on_click=lambda e, cid=chat["id"]: self.delete_chat(cid)
                    )
                )
            )
        self.page.update()

    def load_chat(self, chat_id):
        """Load an existing chat session"""
        self.current_chat_id.value = chat_id
        session = next((s for s in self.chat_sessions.value if s["id"] == chat_id), None)
        if session:
            self.chat_history.controls.clear()
            for message in session["messages"]:
                self.display_message(message)
            self.page.update()

    def display_message(self, message):
        """Display a message in the chat history"""
        is_user = message["sender"] == "user"
        display_name = self.user_name.value if is_user else "AI"
        
        # Calculate available width accounting for sidebar
        available_width = self.page.width - 320  # 300px sidebar + 20px padding
        
        message_container = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(
                        f"{display_name}: {message['text']}",
                        color=ft.Colors.WHITE,
                        width=available_width * 0.6  # Use 60% of available space
                    ),
                    bgcolor=ft.Colors.BLUE_700 if is_user else ft.Colors.GREEN_900,  # Change user background to BLUE_700
                    padding=10,
                    border_radius=10,
                    margin=ft.margin.only(
                        left=100 if is_user else 20,
                        right=20 if is_user else 100,
                        top=5,
                        bottom=5
                    ),
                    width=available_width * 0.6,
                    alignment=ft.alignment.top_left
                ),
                ft.IconButton(
                    icon=ft.Icons.CONTENT_COPY,
                    on_click=lambda e: self.copy_message(message['text'])
                )
            ],
            alignment=ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START
        )
        
        self.chat_history.controls.append(message_container)
        self.page.update()
        self.chat_history.scroll_to(offset=0, duration=300)  # Force scroll to bottom

    def copy_message(self, text):
        """Copy message text to clipboard"""
        self.page.set_clipboard(text)  # Use Flet's method to set clipboard
        self.show_error("Message copied to clipboard!", ft.Colors.GREEN)  # Show confirmation message

    # -- Message Handling --
    def handle_send_message(self, e):
        """Handle sending a message"""
        if not self.validate_send_conditions():
            return

        prompt = self.chat_input.value.strip()
        self.display_user_message(prompt)
        
        # Display the AI thinking message with a spinning wheel
        self.ai_thinking_container = ft.Row(
            controls=[
                ft.Text("🤔 Ai Ron is thinking...", color=ft.Colors.WHITE),
                ft.ProgressRing(
                    width=16,
                    height=16,
                    stroke_width=2,
                    color=ft.Colors.BLUE_200
                )
            ],
            alignment=ft.MainAxisAlignment.START
        )
        self.chat_history.controls.append(self.ai_thinking_container)
        self.page.update()
        
        # Process the AI response
        self.process_ai_response(prompt)
        self.chat_input.value = ""
        self.chat_input.focus()
        self.page.update()

    def display_user_message(self, prompt):
        """Display user message in chat history"""
        self.add_message_to_session("user", prompt)
        self.display_message({"sender": "user", "text": prompt})

    def process_ai_response(self, prompt):
        """Process AI response with typing simulation"""
        def process():
            try:
                selected_model = self.current_model.current.value
                if not selected_model:
                    self.page.run_task(lambda: self.show_error("No model selected!"))
                    return

                data = {"model": selected_model, "prompt": prompt, "stream": True}
                response = requests.post(self.ollama_url, json=data, stream=True, timeout=30)
                
                # Always remove thinking spinner when done
                def cleanup():
                    if hasattr(self, 'ai_thinking_container') and \
                       self.ai_thinking_container in self.chat_history.controls:
                        self.chat_history.controls.remove(self.ai_thinking_container)
                        self.page.update()

                if response.status_code != 200:
                    error_details = {"status": response.status_code, "response": response.text[:200]}
                    async def show_api_error():
                        cleanup()
                        self.show_error(f"API Error: {error_details}", ft.Colors.ORANGE)
                    self.page.run_task(show_api_error)
                    return

                full_response = []
                first_chunk = [True]
                
                try:
                    for line in response.iter_lines():
                        if line:
                            chunk = json.loads(line.decode('utf-8'))
                            if "response" in chunk:
                                for char in chunk["response"]:
                                    full_response.append(char)
                                    async def update_char(fc=first_chunk[0]):
                                        await self.update_ai_message(''.join(full_response), fc)
                                        first_chunk[0] = False
                                    self.page.run_task(update_char)
                                    time.sleep(0.001)
                            elif "error" in chunk:
                                async def show_error():
                                    cleanup()
                                    self.show_error(f"AI Error: {chunk['error']}")
                                self.page.run_task(show_error)
                                return
                except Exception as e:
                    async def handle_error():
                        cleanup()
                        self.show_error(f"Processing Error: {str(e)}")
                    self.page.run_task(handle_error)
                    return

                # Final cleanup
                async def finalize():
                    cleanup()
                    self.add_message_to_session("ai", ''.join(full_response))
                self.page.run_task(finalize)
                
            except Exception as e:
                async def handle_general_error():
                    cleanup()
                    self.show_error(f"Error: {str(e)}")
                self.page.run_task(handle_general_error)

        threading.Thread(target=process, daemon=True).start()

    async def update_ai_message(self, text, first_chunk=False):
        """Update AI message in UI with typing effect"""
        async def update():
            if first_chunk:
                # Create persistent message container
                self.ai_message_container = ft.Container(
                    content=ft.Text(
                        f"AI: {text}",
                        color=ft.Colors.WHITE,
                        width=self.page.width * 0.6
                    ),
                    bgcolor=ft.Colors.GREEN_600,  # Set AI message background to dark green
                    padding=10,
                    border_radius=10,
                    margin=ft.margin.only(right=100),
                    width=self.page.width * 0.6,
                    alignment=ft.alignment.top_left
                )
                self.chat_history.controls.append(self.ai_message_container)
            else:
                # Update existing container
                self.ai_message_container.content.value = f"AI: {text}"
            
            self.page.update()
            self.chat_history.scroll_to(offset=0, duration=300)

        self.page.run_task(update)

    def add_message_to_session(self, sender, text):
        """Add message to current chat session"""
        session = next((s for s in self.chat_sessions.value if s["id"] == self.current_chat_id.value), None)
        if session:
            session["messages"].append({
                "sender": sender,
                "text": text,
                "timestamp": datetime.datetime.now().isoformat()
            })

    def update_session_message(self, sender, text):
        """Update the last message in the session"""
        session = next((s for s in self.chat_sessions.value if s["id"] == self.current_chat_id.value), None)
        if session and session["messages"]:
            session["messages"][-1]["text"] = text

    # -- Chat Management --
    def show_chat_context_menu(self, e, chat_id):
        """Show context menu for chat session"""
        self.selected_chat_id.value = chat_id
        menu = ft.ContextMenu(
            content=ft.Column([
                ft.TextButton("Copy Chat", on_click=self.copy_chat),
                ft.TextButton("Export Chat", on_click=self.export_chat),
                ft.TextButton("Delete Chat", on_click=self.delete_chat),
            ]),
            left=e.global_x,
            top=e.global_y,
        )
        self.page.show_context_menu(menu)

    def copy_chat(self, e):
        """Copy chat to clipboard"""
        if not self.selected_chat_id.value:
            self.show_error("No chat selected!")
            return

        session = next((s for s in self.chat_sessions.value if s["id"] == self.selected_chat_id.value), None)
        if session:
            try:
                chat_text = "\n".join([f"{msg['sender']}: {msg['text']}" for msg in session["messages"]])
                self.page.set_clipboard(chat_text)
                self.show_error("Chat copied to clipboard!", ft.Colors.GREEN)
            except Exception as e:
                self.show_error(f"Copy failed: {str(e)}")

    def export_chat(self, e):
        """Export selected chat to file"""
        if not self.selected_chat_id.value:
            self.show_error("No chat selected!")
            return

        session = next((s for s in self.chat_sessions.value if s["id"] == self.selected_chat_id.value), None)
        if session:
            try:
                filename = f"chat_{session['id']}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
                with open(filename, "w") as f:
                    for msg in session["messages"]:
                        f.write(f"{msg['sender']}: {msg['text']}\n")
                webbrowser.open(filename)
                self.show_error(f"Chat exported to {filename}", ft.Colors.GREEN)
            except Exception as e:
                self.show_error(f"Export failed: {str(e)}")

    def delete_chat(self, chat_id):
        """Delete a chat session"""
        self.chat_sessions.value = [s for s in self.chat_sessions.value if s["id"] != chat_id]
        if self.current_chat_id.value == chat_id:
            self.handle_clear_chat(None)  # Clear chat if the current chat is deleted
            self.current_chat_id.value = None
        self.update_chat_list()
        self.show_error("Chat deleted successfully!", ft.Colors.GREEN)
        self.save_chat_history()  # Save chat history after deletion

    def handle_clear_chat(self, e):
        """Clear current chat display"""
        self.chat_history.controls.clear()
        self.page.update()

    # -- Settings Dialog --
    def show_settings_dialog(self, e):
        """Show settings dialog"""
        def save_settings(e):
            self.user_name.value = name_field.value
            self.ai_thinking_message.value = thinking_field.value
            dlg.open = False
            self.refresh_chat_display()
            self.page.update()

        name_field = ft.TextField(label="User Name", value=self.user_name.value)
        thinking_field = ft.TextField(label="AI Thinking Message", value=self.ai_thinking_message.value)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Settings"),
            content=ft.Column([name_field, thinking_field], tight=True),
            actions=[
                ft.TextButton("Save", on_click=save_settings),
                ft.TextButton("Cancel", on_click=lambda e: setattr(dlg, "open", False))
            ]
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def refresh_chat_display(self):
        """Refresh chat display with updated names"""
        if self.current_chat_id.value:
            # Clear and reload messages with updated names
            self.chat_history.controls.clear()
            session = next((s for s in self.chat_sessions.value if s["id"] == self.current_chat_id.value), None)
            if session:
                for message in session["messages"]:
                    self.display_message(message)
            self.page.update()

    # -- Error Handling --
    def show_error(self, message, color=ft.Colors.RED):
        """Display error message"""
        self.chat_history.controls.append(
            ft.Container(
                content=ft.Text(message, color=ft.Colors.WHITE),
                bgcolor=color,
                padding=10,
                border_radius=10,
                margin=ft.margin.only(right=100)
            )
        )
        self.page.update()

    def validate_send_conditions(self):
        """Validate conditions for sending a message"""
        if not self.current_model.current.value:
            self.show_error("Please select a model first!", ft.Colors.RED)
            return False
        if not any(opt.key == self.current_model.current.value for opt in self.current_model.current.options):
            self.show_error("Selected model not available!", ft.Colors.RED)
            return False
        if not self.chat_input.value.strip():
            return False
        return True

    def save_chat_history(self):
        """Save chat sessions to a JSON file"""
        with open("chat_history.json", "w") as f:
            json.dump(self.chat_sessions.value, f)

    def load_chat_history(self):
        """Load chat sessions from a JSON file"""
        if os.path.exists("chat_history.json"):
            with open("chat_history.json", "r") as f:
                self.chat_sessions.value = json.load(f)

def main(page: ft.Page):
    # Set the icon for the application
    page.icon = "OIP-C.jpg"  # Ensure this path is correct

    chat_app = ChatApp(page)

if __name__ == "__main__":
    ft.app(target=main)
