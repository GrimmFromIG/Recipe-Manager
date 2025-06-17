import streamlit as st
import requests
from typing import List, Dict

# Configuration
API_KEY = "328993ee5d0743ca8cfdc2a53f79f93a"  
BASE_URL = "https://api.spoonacular.com/recipes"

# Initialize session state
if 'selected_recipe' not in st.session_state:
    st.session_state.selected_recipe = None
if 'favorites' not in st.session_state:
    st.session_state.favorites = []
if 'view_favorites' not in st.session_state:
    st.session_state.view_favorites = False

class FavoritesManager:
    """ADT for managing favorite recipes"""
    
    def __init__(self):
        self.favorites = st.session_state.favorites
    
    def add(self, recipe: Dict) -> None:
        """Add recipe to favorites if not already present"""
        if not any(fav['id'] == recipe['id'] for fav in self.favorites):
            # Store only essential recipe data to save space
            compact_recipe = {
                'id': recipe['id'],
                'title': recipe['title'],
                'image': recipe.get('image', ''),
                'readyInMinutes': recipe['readyInMinutes'],
                'servings': recipe['servings']
            }
            self.favorites.append(compact_recipe)
            st.session_state.favorites = self.favorites
            st.toast("❤️ Added to favorites!", icon="✅")
        else:
            st.toast("⚠️ Already in favorites", icon="ℹ️")
    
    def remove(self, recipe_id: int) -> None:
        """Remove recipe from favorites"""
        self.favorites = [fav for fav in self.favorites if fav['id'] != recipe_id]
        st.session_state.favorites = self.favorites
        st.toast("🗑️ Removed from favorites", icon="✅")
    
    def get_all(self) -> List[Dict]:
        """Get all favorite recipes"""
        return self.favorites
    
    def is_favorite(self, recipe_id: int) -> bool:
        """Check if recipe is in favorites"""
        return any(fav['id'] == recipe_id for fav in self.favorites)

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

def display_recipe_card(recipe, favorites_manager):
    """Display a compact recipe card"""
    with st.container(border=True):
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(recipe.get("image", ""), width=150)
        with col2:
            st.subheader(recipe["title"])
            st.caption(f"⏱️ {recipe['readyInMinutes']} min | 🍽️ {recipe['servings']} servings")
            
            # Favorite toggle
            fav_col, btn_col = st.columns([1, 1])
            with fav_col:
                if favorites_manager.is_favorite(recipe['id']):
                    if st.button("❤️ Remove", key=f"unfav_{recipe['id']}", use_container_width=True):
                        favorites_manager.remove(recipe['id'])
                        st.rerun()
                else:
                    if st.button("♡ Add", key=f"fav_{recipe['id']}", use_container_width=True):
                        favorites_manager.add(recipe)
                        st.rerun()
            
            with btn_col:
                if st.button("View Details", key=f"view_{recipe['id']}", use_container_width=True):
                    with st.spinner("Loading recipe..."):
                        detailed_recipe = get_recipe_details(recipe["id"])
                        if detailed_recipe:
                            st.session_state.selected_recipe = detailed_recipe
                            st.rerun()

def display_recipe_details(recipe, favorites_manager):
    """Display full recipe details"""
    st.button("← Back to results", on_click=lambda: st.session_state.update(selected_recipe=None))
    
    # Header with favorite control
    col_title, col_fav = st.columns([4, 1])
    with col_title:
        st.subheader(recipe["title"])
    with col_fav:
        if favorites_manager.is_favorite(recipe['id']):
            if st.button("❤️ Remove from Favorites", use_container_width=True):
                favorites_manager.remove(recipe['id'])
                st.rerun()
        else:
            if st.button("♡ Add to Favorites", use_container_width=True):
                favorites_manager.add(recipe)
                st.rerun()
    
    st.image(recipe.get("image", ""), width=400)
    
    # Quick facts
    cols = st.columns(4)
    cols[0].metric("Prep Time", f"{recipe['readyInMinutes']} min")
    cols[1].metric("Servings", recipe['servings'])
    if 'healthScore' in recipe:
        cols[2].metric("Health Score", f"{recipe['healthScore']}/100")
    if 'pricePerServing' in recipe:
        cols[3].metric("Price", f"${recipe['pricePerServing']/100:.2f}")
    
    st.divider()
    
    # Ingredients and Instructions in tabs
    tab_ing, tab_inst, tab_nut = st.tabs(["Ingredients", "Instructions", "Nutrition"])
    
    with tab_ing:
        st.subheader("Ingredients")
        for ingredient in recipe["extendedIngredients"]:
            st.markdown(f"▪️ {ingredient['original']}")
    
    with tab_inst:
        st.subheader("Instructions")
        if recipe["instructions"]:
            instructions = recipe["instructions"]
            # Clean HTML tags if present
            instructions = instructions.replace("<ol>", "").replace("</ol>", "").replace("<li>", "▸ ").replace("</li>", "\n\n")
            st.markdown(instructions)
        else:
            st.warning("No instructions available")
    
    with tab_nut:
        st.subheader("Nutrition")
        if 'nutrition' in recipe:
            nutrients = recipe['nutrition']['nutrients']
            for nut in nutrients[:10]:  # Show top 10 nutrients
                st.progress(float(nut['percentOfDailyNeeds']/100), 
                           text=f"{nut['name']}: {nut['amount']} {nut['unit']} ({nut['percentOfDailyNeeds']:.0f}% DV)")
        else:
            st.info("Nutrition information not available")
    
    if recipe.get("sourceUrl"):
        st.divider()
        st.markdown(f"🔗 [Original Recipe Source]({recipe['sourceUrl']})")

# Streamlit UI Configuration
st.set_page_config(
    page_title="Recipe Manager", 
    page_icon="🍳", 
    layout="wide",
    menu_items={
        'About': "### 🍳 Recipe Manager\nFind and save your favorite recipes!"
    }
)

# Custom CSS
st.markdown("""
<style>
    .recipe-card {
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
    }
    .stTabs [role=tablist] {
        gap: 10px;
    }
    .stTabs [role=tab] {
        padding: 8px 12px;
        border-radius: 8px 8px 0 0;
    }
    .stTabs [aria-selected=true] {
        background-color: #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)

# Main App
st.title("🍳 Recipe Manager")
st.caption("Discover and save your favorite recipes")

# Initialize favorites manager
favorites_manager = FavoritesManager()

# Navigation
tab_search, tab_favorites = st.tabs(["🔍 Search Recipes", "❤️ My Favorites"])

with tab_search:
    # Search form
    with st.form("search_form"):
        col1, col2 = st.columns(2)
        with col1:
            query = st.text_input("Recipe name", placeholder="e.g. pasta, salad...")
        with col2:
            ingredients = st.text_input("Ingredients (comma separated)", placeholder="e.g. tomato, cheese...")
        
        search_submitted = st.form_submit_button("Search Recipes", type="primary")

    # Display results or details
    if st.session_state.selected_recipe:
        display_recipe_details(st.session_state.selected_recipe, favorites_manager)
    elif search_submitted:
        if not query and not ingredients:
            st.warning("Please enter at least one search criteria")
        else:
            with st.spinner("🔍 Searching recipes..."):
                recipes = search_recipes(query, ingredients)
            
            if recipes:
                st.subheader("Search Results")
                for recipe in recipes:
                    display_recipe_card(recipe, favorites_manager)
            else:
                st.info("No recipes found. Try different search terms.")
    else:
        # Initial state with examples
        with st.expander("💡 Search examples", expanded=True):
            examples = st.columns(3)
            examples[0].button("Quick Meals", 
                              on_click=lambda: st.session_state.update(query="quick meals"))
            examples[1].button("Vegetarian", 
                              on_click=lambda: st.session_state.update(query="vegetarian"))
            examples[2].button("Chicken Recipes", 
                              on_click=lambda: st.session_state.update(query="chicken"))
        
        st.info("Enter search criteria to find recipes")

with tab_favorites:
    if not favorites_manager.get_all():
        st.info("Your favorites list is empty. Save recipes by clicking the ❤️ button.")
        if st.button("Explore Recipes", type="primary"):
            st.session_state.view_favorites = False
            st.rerun()
    else:
        st.subheader(f"❤️ Your Favorite Recipes ({len(favorites_manager.get_all())})")
        
        # Filter and sort options
        with st.expander("🔍 Filter/Sort"):
            col_sort, col_filter = st.columns(2)
            with col_sort:
                sort_option = st.selectbox("Sort by", 
                                         ["Recently Added", "Prep Time (Low to High)", "A-Z"])
            with col_filter:
                filter_text = st.text_input("Filter by name")
        
        # Apply filters/sort
        fav_recipes = favorites_manager.get_all()
        
        if filter_text:
            fav_recipes = [r for r in fav_recipes if filter_text.lower() in r['title'].lower()]
        
        if sort_option == "Recently Added":
            pass  # Default order is recently added
        elif sort_option == "Prep Time (Low to High)":
            fav_recipes.sort(key=lambda x: x['readyInMinutes'])
        elif sort_option == "A-Z":
            fav_recipes.sort(key=lambda x: x['title'])
        
        # Display favorites
        if not fav_recipes and filter_text:
            st.warning("No favorites match your filter")
        else:
            for recipe in fav_recipes:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([1, 3, 1])
                    with col1:
                        st.image(recipe.get("image", ""), width=120)
                    with col2:
                        st.subheader(recipe["title"])
                        st.caption(f"⏱️ {recipe['readyInMinutes']} min | 🍽️ {recipe['servings']} servings")
                    with col3:
                        if st.button("View", key=f"view_fav_{recipe['id']}"):
                            detailed_recipe = get_recipe_details(recipe["id"])
                            if detailed_recipe:
                                st.session_state.selected_recipe = detailed_recipe
                                st.rerun()
                        if st.button("Remove", key=f"remove_fav_{recipe['id']}", type="secondary"):
                            favorites_manager.remove(recipe['id'])
                            st.rerun()