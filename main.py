from fasthtml.common import *
import pandas as pd

app, rt = fast_app(
    pico=False,
    hdrs=(Link(rel="stylesheet", href="static/style.css"), Script(src="https://unpkg.com/htmx.org@1.8.4"))
)

talks = pd.read_csv("combined_data.csv").to_dict(orient="records")

# Get valid talks only
valid_talks = [t for t in talks if pd.notna(t.get('talk_title')) and pd.notna(t.get('speaker_name'))]

# Extract unique session topics for filtering
session_topics = sorted(set(
    topic.strip()
    for talk in talks 
    if pd.notna(talk.get('session_topics'))
    for topic in talk['session_topics'].split(',')
))

def create_talk_cards(filtered_talks):
    return [
        Article(
            Header(H3(talk["talk_title"])),
            P(f"Speaker: {talk['speaker_name']}"),
            A("Replay Session", href=f"/talk/{talk['video_id']}", cls="button")
        )
        for talk in filtered_talks
    ]

@rt("/")
def get():
    talk_cards = create_talk_cards(valid_talks)
    
    return Titled("Conference Talks",
        Div(
            Div(
                Form(
                    Input(type="text", id="search", name="search", placeholder="Search talks...",
                          hx_get="/filter", hx_target="#talk-list", hx_trigger="input changed delay:500ms"),
                    hx_get="/filter", hx_target="#talk-list"
                ),
                Div(
                    Button("All", hx_get="/filter", hx_target="#talk-list", hx_trigger="click", 
                          cls="topic-button active"),  # Add active class to All button
                    *[Button(topic, hx_get="/filter", hx_target="#talk-list", hx_trigger="click", 
                            hx_vars=f"topic:'{topic}'", cls="topic-button") for topic in session_topics],
                    cls="topic-filters"
                ),
                cls="filters"
            ),
            Div(*talk_cards, id="talk-list", cls="talk-list"),
            cls="container"
        )
    )

@rt("/filter")
def get(search: str = "", topic: str = ""):
    filtered_talks = valid_talks.copy()
    
    if search:
        search = search.lower()
        filtered_talks = [
            t for t in filtered_talks 
            if search in str(t['talk_title']).lower() or 
               search in str(t['speaker_name']).lower() or 
               (pd.notna(t.get('description')) and search in str(t['description']).lower())
        ]
    
    if topic:
        filtered_talks = [
            t for t in filtered_talks 
            if pd.notna(t.get('session_topics')) and topic in str(t['session_topics'])
        ]
    
    return Div(*create_talk_cards(filtered_talks), cls="talk-list")

@rt("/talk/{video_id}")
def get(video_id: str):
    talk = next((t for t in talks if t["video_id"] == video_id), None)
    if not talk:
        return Titled("Talk Not Found", P("Sorry, this talk does not exist."))

    return Titled(str(talk["talk_title"]),
        Article(
            Header(H2(talk["talk_title"])),
            Div(
                Iframe(src=f"https://www.youtube.com/embed/{talk['video_id']}", width="560", height="315"),
                P(talk["description"] if pd.notna(talk.get('description')) else ""),
                P(B("Speaker: "), talk["speaker_name"]),
                P(B("Topics: "), talk["session_topics"] if pd.notna(talk.get('session_topics')) else ""),
                cls="talk-detail"
            )
        )
    )

serve()