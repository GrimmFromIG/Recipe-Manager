import streamlit as st
import requests
from typing import List, Dict, Optional

# API config
API_KEY = "328993ee5d0743ca8cfdc2a53f79f93a"
BASE_URL = "https://api.spoonacular.com/recipes"

# Initialize session
def init_session_state():
    if 'favorites' not in st.session_state:
        st.session_state.favorites = []
    if 'selected_recipe_id' not in st.session_state:
        st.session_state.selected_recipe_id = None
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []

init_session_state()

class FavoriteRecipesCollection:
    """ADT for managing favorite recipes"""
    
    def add(self, recipe: Dict) -> None:
        """Add recipe to favorites"""
        if not any(fav['id'] == recipe['id'] for fav in st.session_state.favorites):
            compact_recipe = {
                'id': recipe['id'],
                'title': recipe['title'],
                'image': recipe.get('image', ''),
                'readyInMinutes': recipe['readyInMinutes'],
                'servings': recipe['servings']
            }
            st.session_state.favorites.append(compact_recipe)
            st.toast("Added to favorites!", icon="✅")
    
    def remove(self, recipe_id: int) -> None:
        """Remove recipe from favorites"""
        st.session_state.favorites = [fav for fav in st.session_state.favorites if fav['id'] != recipe_id]
        st.toast("Removed from favorites", icon="❌")
    
    def contains(self, recipe_id: int) -> bool:
        """Check if recipe is in favorites"""
        return any(fav['id'] == recipe_id for fav in st.session_state.favorites)
    
    def get_all(self) -> List[Dict]:
        """Get all favorite recipes"""
        return st.session_state.favorites

def search_recipes(query="", ingredients=""):
    """Search recipes using Spoonacular API"""
    params = {
        "apiKey": API_KEY,
        "addRecipeInformation": True,
        "fillIngredients": True,
        "number": 10
    }
    
    if query:
        params["query"] = query
    if ingredients:
        params["includeIngredients"] = ingredients
    
    try:
        response = requests.get(f"{BASE_URL}/complexSearch", params=params)
        response.raise_for_status()
        st.session_state.search_results = response.json().get("results", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Error searching recipes: {e}")
        st.session_state.search_results = []

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

def display_recipe_card(recipe, favorites_manager):
    """Display a compact recipe card"""
    with st.container(border=True):
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(recipe.get("image", ""), width=150)
        with col2:
            st.subheader(recipe["title"])
            st.caption(f"⏱️ {recipe['readyInMinutes']} min | 🍽️ {recipe['servings']} servings")
            
            # Favorite button - using callbacks to prevent rerun
            if favorites_manager.contains(recipe['id']):
                st.button(
                    "❤️ Remove from favorites",
                    key=f"unfav_{recipe['id']}",
                    on_click=lambda: favorites_manager.remove(recipe['id'])
                )
            else:
                st.button(
                    "♡ Add to favorites",
                    key=f"fav_{recipe['id']}",
                    on_click=lambda: favorites_manager.add(recipe)
                )
            
            st.button(
                "🔍 View details",
                key=f"details_{recipe['id']}",
                on_click=lambda: st.session_state.update(selected_recipe_id=recipe['id'])
            )

def display_recipe_details(recipe_id, favorites_manager):
    """Display full recipe details"""
    recipe = get_recipe_details(recipe_id)
    if not recipe:
        st.error("Recipe not found")
        return
    
    st.button(
        "← Back to results",
        on_click=lambda: st.session_state.pop('selected_recipe_id')
    )
    
    col_title, col_fav = st.columns([4, 1])
    with col_title:
        st.title(recipe["title"])
    with col_fav:
        if favorites_manager.contains(recipe['id']):
            st.button(
                "❤️ Remove from Favorites",
                on_click=lambda: favorites_manager.remove(recipe['id']),
                use_container_width=True
            )
        else:
            st.button(
                "♡ Add to Favorites",
                on_click=lambda: favorites_manager.add(recipe),
                use_container_width=True
            )
    
    # Details display etc.
    st.image(recipe.get("image", ""), width=400)
    
    with st.expander("📝 Ingredients"):
        for ing in recipe['extendedIngredients']:
            st.markdown(f"- {ing['original']}")
    
    with st.expander("📋 Instructions"):
        if recipe["instructions"]:
            instructions = recipe["instructions"].replace("<ol>", "").replace("</ol>", "").replace("<li>", "▸ ")
            st.markdown(instructions)
        else:
            st.warning("No instructions available")

# Main App
st.set_page_config(page_title="Recipe Manager", page_icon="🍳", layout="wide")

# Initialize favorites manager
favorites_manager = FavoriteRecipesCollection()

# Navigation
tab1, tab2, tab3 = st.tabs(["🔍 Search Recipes", "❤️ My Favorites", "📚 About"])

with tab1:
    # Search form
    with st.form("search_form"):
        col1, col2 = st.columns(2)
        with col1:
            query = st.text_input("Recipe name")
        with col2:
            ingredients = st.text_input("Ingredients (comma separated)")
        
        submitted = st.form_submit_button("Search Recipes")
    
    # Display results or details
    if st.session_state.selected_recipe_id:
        display_recipe_details(st.session_state.selected_recipe_id, favorites_manager)
    elif submitted:
        if not query and not ingredients:
            st.warning("Please enter search criteria")
        else:
            with st.spinner("Searching recipes..."):
                search_recipes(query, ingredients)
            
            if st.session_state.search_results:
                st.subheader("Search Results")
                for recipe in st.session_state.search_results:
                    display_recipe_card(recipe, favorites_manager)
            else:
                st.info("No recipes found")

with tab2:
    st.subheader("❤️ My Favorite Recipes")
    
    if not favorites_manager.get_all():
        st.info("Your favorites list is empty")
    else:
        for recipe in favorites_manager.get_all():
            with st.container(border=True):
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    st.image(recipe.get("image", ""), width=120)
                with col2:
                    st.subheader(recipe["title"])
                    st.caption(f"⏱️ {recipe['readyInMinutes']} min | 🍽️ {recipe['servings']} servings")
                with col3:
                    st.button(
                        "View Details",
                        key=f"view_fav_{recipe['id']}",
                        on_click=lambda r=recipe: st.session_state.update(selected_recipe_id=r['id'])
                    )
                    st.button(
                        "Remove",
                        key=f"remove_fav_{recipe['id']}",
                        on_click=lambda r=recipe: favorites_manager.remove(r['id'])
                    )

with tab3:
    st.title("About Recipe Manager")
    st.markdown("""
    This application allows you to search for recipes, view details, and manage your favorite recipes.
    
    **Features:**
    - Search recipes by name or ingredients
    - View detailed recipe information
    - Add/remove recipes from favorites
    - Responsive design for easy navigation
    
    **API Used:**
    - Spoonacular API for recipe data
    
    **Built with:**
    - Streamlit for the web interface
                
    **Creator**
    - Bohdan Petroshchuk
    """)