# main runner 

import gradio as gr
from fastapi import FastAPI
import uvicorn
from prompts import APPNAME, HELPME
from econapp import init_or_load_collection, chat_handler

# build the gradio app
def build_gradio_app():
    collection = init_or_load_collection()

    with gr.Blocks(title=APPNAME) as econchatapp:
        gr.Markdown(f"# {APPNAME}\n\n{HELPME}")

        state = gr.State({})

        # make a chat interface. adjust height and size
        gr.ChatInterface(
            fn=lambda msg, hist, st: chat_handler(collection, msg, hist, st),
            chatbot=gr.Chatbot(height=300, type="messages"),
            additional_inputs=[state],
            additional_outputs=[state],
            type="messages",
        )

    return econchatapp

# main runner
# this should run on http://127.0.0.1:8000/econapp
def main():
    demo = build_gradio_app()
    api = FastAPI()
    # run add at url 
    api = gr.mount_gradio_app(api, demo, path="/econapp")
    # run on local port 8000
    uvicorn.run(api, host="127.0.0.1", port=8000)
    


if __name__ == "__main__":
    main()