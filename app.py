import streamlit as st
from pymongo import MongoClient
import datetime
import pandas as pd

# Connect to MongoDB
mongo_uri = "mongodb+srv://root1:1234@cluster0.bcqibzg.mongodb.net/INVENTORY-MANAGE"
client = MongoClient(mongo_uri)
db = client['INVENTORY-MANAGE']
products_collection = db['products']
sales_collection = db['sales']

# Define the username and password
correct_username = "admin"
correct_password = "admin"

# Function to fetch data from MongoDB and return it as a Pandas DataFrame
def fetch_data_as_dataframe(collection):
    data = list(collection.find())
    df = pd.DataFrame(data)
    return df

# Create a login page
st.sidebar.title("Login")
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

if username == correct_username and password == correct_password:
    st.sidebar.success("Login successful!")
    page = st.sidebar.radio("Select a page", ["All Fields", "Add Product", "Record Sales", "Dashboard"])
else:
    st.sidebar.error("Login failed. Please provide the correct username and password.")
    st.stop()

# Continue with the rest of the code only if login is successful

# Sidebar
if page == "All Fields":
    st.title("All Fields")
    all_fields = products_collection.find()
    for field in all_fields:
        st.write(f"Product: {field['name']}, Quantity: {field['qty']}, Price: {field['price']}")

# Add Product
elif page == "Add Product":
    st.title("Add Product")
    product_name = st.text_input("Product Name")
    product_qty = st.number_input("Product Quantity", value=1)
    product_price = st.number_input("Product Price")

    # Suggest existing product names
    product_names = [product["name"] for product in products_collection.find()]
    selected_product_name = st.selectbox("Select from existing products", ["Create New"] + product_names, key='existing_products')

    existing_product_data = None
    if selected_product_name != "Create New":
        existing_product_data = products_collection.find_one({"name": selected_product_name})

    if existing_product_data:
        st.write(f"Previous Quantity: {existing_product_data['qty']}, Previous Price: {existing_product_data['price']}")

    if st.button("Add Product"):
        if existing_product_data:
            # Update existing product
            updated_qty = existing_product_data["qty"] + product_qty
            updated_price = product_price
            products_collection.update_one({"name": selected_product_name}, {"$set": {"qty": updated_qty, "price": updated_price}})
            st.success(f"Updated {selected_product_name} with new quantity and price.")
        else:
            if product_name:
                # Create a new product
                product_data = {
                    "name": product_name,
                    "qty": product_qty,
                    "price": product_price,
                    "added_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Record added date
                }
                products_collection.insert_one(product_data)
                st.success(f"Added {product_data['name']} to the inventory.")
            else:
                st.error("Please enter a product name to create a new product.")

# Record Sales
elif page == "Record Sales":
    st.title("Record Sales")
    product_options = [product["name"] for product in products_collection.find()]
    selected_product = st.selectbox("Select Product for Sales", product_options)
    sales_qty = st.number_input("Sales Quantity", value=1)
    sales_price = st.number_input("Sales Price")

    if st.button("Record Sales"):
        product_data = products_collection.find_one({"name": selected_product})
        if product_data:
            available_qty = product_data["qty"] - sales_qty

            if available_qty >= 0:
                sales_data = {
                    "product_name": selected_product,
                    "qty": sales_qty,
                    "price": sales_price,
                    "date": datetime.datetime.now()
                }
                sales_collection.insert_one(sales_data)
                st.success(f"Sales recorded for {selected_product}.")

                # Update product quantity in the product collection
                products_collection.update_one({"name": selected_product}, {"$set": {"qty": available_qty}})
            else:
                st.error(f"Insufficient quantity for {selected_product}.")
        else:
            st.error(f"Product not found in the inventory.")

# Dashboard
elif page == "Dashboard":
    st.title("Dashboard")

    # Product details
    st.subheader("Product Details")
    product_df = fetch_data_as_dataframe(products_collection)
    st.dataframe(product_df)  # Display product data in a Pandas DataFrame

    # Sales details
    st.subheader("Sales Details")
    sales_df = fetch_data_as_dataframe(sales_collection)
    st.dataframe(sales_df)  # Display sales data in a Pandas DataFrame

    # Total quantities and prices
    total_purchase_qty = product_df['qty'].sum()
    total_purchase_price = (product_df['qty'] * product_df['price']).sum()

    total_sales_qty = sales_df['qty'].sum()
    total_sales_price = (sales_df['qty'] * sales_df['price']).sum()

    st.subheader("Total Purchase and Sales")
    st.write(f"Total Purchase Quantity: {total_purchase_qty}")
    st.write(f"Total Purchase Price: {total_purchase_price}")
    st.write(f"Total Sales Quantity: {total_sales_qty}")
    st.write(f"Total Sales Price: {total_sales_price}")
