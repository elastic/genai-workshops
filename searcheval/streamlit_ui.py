import streamlit as st

st.set_page_config(
    page_title="streamlit ui",
    page_icon="👋",
    initial_sidebar_state= "expanded"
)


st.sidebar.success("Select a demo above to get started!")

with st.container():
    import streamlit as st
    st.image("1_logo.jpg")

    st.markdown(
        """
        <style>
        .scrolling-text {
            font-family: 'Courier New', Courier, monospace;
            color: yellow;
            text-align: center;
            animation: scroll 20s linear infinite;
            background-color: black;
            padding: 20px;
        }

        @keyframes scroll {
            0% { transform: translateY(100%); }
            100% { transform: translateY(-100%); }
        }
        </style>
        <div class="scrolling-text">
            <br>
            <h3>Episode 2025</h3>
            <h3>THE SEARCH AWAKENS</h3>
            <br>
            <p>It is a time of desperate queries.<br>
            Underperforming results plague the galaxy of data,<br>
            leaving users frustrated and unsatisfied.<br>
            But hope glimmers on the horizon!</p>
            <br>
            <p>A brave alliance of analyzers,<br>
            led by the valiant Search Practitioners,<br>
            assembles for a new workshop<br>
            to restore balance and relevance to the index.</p>
            <br>
            <p>Their journey begins<br>
            by tuning mappings and queries,<br>
            seeking the hidden power of Boosting,<br>
            unleashing the refined might of Language Analyzers,<br>
            and harnessing the mysterious art of Fuzziness.</p>
            <br>
            <p>Together, they will discover<br>
            how these techniques bolster the might of Vector Search,<br>
            enabling them to cut through the galactic clutter<br>
            with remarkable precision.</p>
            <br>
            <p>Yet this is only the beginning!<br>
            They must learn to Evaluate Search Relevance,<br>
            test the potential of RAG,<br>
            and finally behold<br>
            the triumphant results in an Agentic App.</p>
            <br>
            <p>Now, let us join our heroes<br>
            as they embark on this epic workshop,<br>
            determined to save the galaxy<br>
            — one well-tuned query at a time!</p>
        </div>
        """,
        unsafe_allow_html=True
    )



