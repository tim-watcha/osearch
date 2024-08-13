import streamlit as st

def main():
    st.title("URL Submission App")

    # Create a form
    with st.form(key='url_form'):
        # Add a text input for the URL
        url = st.text_input(label="Enter URL")

        # Add a submit button
        submit_button = st.form_submit_button(label="Submit")

    # Check if the form is submitted
    if submit_button:
        st.success("Submitted!")
        st.write(f"You entered: {url}")

if __name__ == "__main__":
    main()
