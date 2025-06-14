import streamlit as st
import requests
import json

# Configuration
API_KEY = "328993ee5d0743ca8cfdc2a53f79f93a"  
BASE_URL = "https://api.spoonacular.com/recipes"

# Initialize session state
if 'selected_recipe' not in st.session_state:
    st.session_state.selected_recipe = None

def search_recipes(query="", ingredients=""):
    """Search recipes using Spoonacular API"""
    params = {
        "apiKey": API_KEY,
        "addRecipeInformation": True,
        "fillIngredients": True,
        "number": 10  # Limit to 10 results
    }
    
    if query:
        params["query"] = query
    if ingredients:
        params["includeIngredients"] = ingredients
    
    try:
        response = requests.get(f"{BASE_URL}/complexSearch", params=params)
        response.raise_for_status()
        return response.json()["results"]
    except requests.exceptions.RequestException as e:
        st.error(f"Error searching recipes: {e}")
        return []

def get_recipe_details(recipe_id):
    """Get detailed information for a specific recipe"""
    try:
        response = requests.get(
            f"{BASE_URL}/{recipe_id}/information",
            params={"apiKey": API_KEY, "includeNutrition": False}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching recipe details: {e}")
        return None

def display_recipe(recipe):
    """Display recipe details in a formatted way"""
    st.subheader(recipe["title"])
    st.image(recipe.get("image", ""), width=300)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"⏱️ **Ready in:** {recipe['readyInMinutes']} minutes")
    with col2:
        st.markdown(f"🍽️ **Servings:** {recipe['servings']}")
    
    st.markdown("---")
    
    # Ingredients
    st.subheader("Ingredients")
    for ingredient in recipe["extendedIngredients"]:
        st.markdown(f"- {ingredient['original']}")
    
    # Instructions
    st.subheader("Instructions")
    if recipe["instructions"]:
        # Clean up HTML tags if present
        instructions = recipe["instructions"].replace("<ol>", "").replace("</ol>", "").replace("<li>", "- ").replace("</li>", "\n")
        st.markdown(instructions)
    else:
        st.warning("No instructions available for this recipe.")
    
    # Source
    if recipe.get("sourceUrl"):
        st.markdown(f"🔗 [Source]({recipe['sourceUrl']})")

# Streamlit UI
st.set_page_config(page_title="Recipe Manager", page_icon="🍳", layout="wide")
st.title("🍳 Recipe Manager")

# Search form
with st.form("search_form"):
    col1, col2 = st.columns(2)
    with col1:
        query = st.text_input("Search by recipe name")
    with col2:
        ingredients = st.text_input("Search by ingredients (comma separated)")
    
    submitted = st.form_submit_button("Search Recipes")

# Display results or details
if st.session_state.selected_recipe:
    # Show recipe details
    st.button("← Back to results", on_click=lambda: st.session_state.update(selected_recipe=None))
    display_recipe(st.session_state.selected_recipe)
elif submitted:
    # Perform search
    if not query and not ingredients:
        st.warning("Please enter a search term or ingredients")
    else:
        with st.spinner("Searching recipes..."):
            recipes = search_recipes(query, ingredients)
        
        if recipes:
            st.subheader("Search Results")
            for recipe in recipes:
                with st.expander(f"{recipe['title']} (Ready in {recipe['readyInMinutes']} min)"):
                    # Basic info
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if recipe.get("image"):
                            st.image(recipe["image"], width=150)
                    with col2:
                        st.markdown(f"**Servings:** {recipe['servings']}")
                        st.markdown(f"**Missing ingredients:** {', '.join([i['name'] for i in recipe['missedIngredients']])}")
                    
                    # View details button
                    if st.button("View Details", key=f"view_{recipe['id']}"):
                        with st.spinner("Loading recipe details..."):
                            detailed_recipe = get_recipe_details(recipe["id"])
                            if detailed_recipe:
                                st.session_state.selected_recipe = detailed_recipe
                                st.experimental_rerun()
        else:
            st.info("No recipes found matching your criteria.")
else:
    # Initial state
    st.info("Enter search criteria to find recipes")