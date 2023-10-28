import pymongo
import streamlit as st
import datetime
import pandas as pd  # Import pandas library

# Replace with your MongoDB connection string
mongo_uri = "mongodb+srv://root1:1234@cluster0.bcqibzg.mongodb.net/"

# Create a MongoDB client and database
client = pymongo.MongoClient(mongo_uri)
db = client["inventory_db"]

# Set Streamlit page configuration (layout)
st.set_page_config(layout="wide")

# Streamlit app title and sidebar navigation
app_title = "Inventory Management System"

# Define empty lists for product data
product_names = []
product_quantities = []
purchase_requirements = []
sales_quantities = []

# Login page
login = False

if not login:
    st.title(app_title)
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if username == "KAZEM123@" and password == "KAZEM@123":
        login = True

if login:
    login_placeholder = st.empty()  # Create an empty placeholder for the login content
    login_placeholder.empty()  # Clear the login content

    page = st.sidebar.selectbox("Select Page", ["Add Product", "Sales", "Dashboard", "Monthly Report"])

    if page == "Add Product":
        # Page to add products
        st.header("Add Product")

        # Input field for product name with autocomplete
        product_name = st.text_input("Product Name")
        product_name_suggestions = [product["name"] for product in db.products.find({"name": {"$regex": f'^{product_name}', "$options": "i"}})]
        if product_name_suggestions:
            selected_product_name = st.selectbox("Select Product Name", product_name_suggestions, key='product_name_suggestions')
        else:
            selected_product_name = product_name

        product_quantity = st.number_input("Product Quantity", value=0)
        product_price = st.number_input("Product Price", value=0.0)

        if st.button("Add Product"):
            # Check if the product name already exists in the database
            existing_product = db.products.find_one({"name": selected_product_name})

            if existing_product:
                # Product with the same name exists; suggest an update
                st.warning(f"A product with the name '{selected_product_name}' already exists.")
                st.write("You can update the price and quantity of the existing product or choose a different name.")

                update_price = st.number_input("Update Product Price", value=existing_product["price"])
                update_quantity = st.number_input("Update Product Quantity", value=existing_product["quantity"])

                if st.button("Update Product"):
                    # Update the existing product
                    db.products.update_one(
                        {"name": selected_product_name},
                        {"$set": {"quantity": update_quantity, "price": update_price}}
                    )
                    st.success(f"Product '{selected_product_name}' updated successfully.")
            else:
                # Product with the same name doesn't exist; add a new product
                product_data = {
                    "name": selected_product_name,
                    "quantity": product_quantity,
                    "price": product_price,
                    "purchase_date": datetime.datetime.now()  # Add purchase date
                }
                db.products.insert_one(product_data)
                st.success(f"Product '{selected_product_name}' added successfully.")

    elif page == "Sales":
        # Page to process sales
        st.header("Sales")
        st.write("Select the product, enter price, and quantity to process a sale.")

        # Retrieve and display product data
        products = db.products.find()
        product_list = [product["name"] for product in products]

        selected_product = st.selectbox("Select Product", product_list)
        sales_price = st.number_input("Enter Sales Price", value=0.0)
        sales_quantity = st.number_input("Enter Quantity", value=0)

        if st.button("Process Sale"):
            # Update product quantity and calculate sales price in MongoDB
            product_data = db.products.find_one({"name": selected_product})
            if product_data:
                if product_data["quantity"] >= sales_quantity:
                    updated_quantity = product_data["quantity"] - sales_quantity
                    db.products.update_one(
                        {"name": selected_product},
                        {"$set": {"quantity": updated_quantity}}
                    )
                    sales_total = sales_quantity * sales_price
                    st.success(f"Sale processed for {sales_quantity} units of {selected_product}. Sales Price: ${sales_total:.2f}")
                else:
                    st.error(f"Insufficient quantity of {selected_product} in the inventory.")
            else:
                st.error(f"Product '{selected_product}' not found in the inventory.")

    elif page == "Dashboard":
        # Page to show the dashboard
        st.header("Dashboard")

        # Retrieve and display product data
        products = db.products.find()

        for product in products:
            product_names.append(product['name'])
            product_quantities.append(product['quantity'])
            purchase_requirement = max(0, 10 - product['quantity'])  # Purchase requirement if quantity is less than 10
            purchase_requirements.append(purchase_requirement)
            sales_quantities.append(max(0, product['quantity']))  # Sales quantity (non-negative)

        # Create a dictionary to display the data in a table
        data = {
            "Product Name": product_names,
            "Quantity": product_quantities,
            "Sales Product": purchase_requirements,
            "In Stock": sales_quantities
        }

        # Calculate the total purchase quantity and display it
        total_purchase_quantity = sum(product_quantities)
        st.subheader("Total Purchase Quantity:")
        st.write(total_purchase_quantity)

        # Display the data in a table
        st.table(data)

        st.subheader("Total Products in Inventory:")
        total_products = sum(product_quantities)
        st.write(total_products)

    elif page == "Monthly Report":
        # Page to generate the monthly report
        st.header("Monthly Report")
        month = st.selectbox("Select Month", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
        year = st.number_input("Enter Year", value=datetime.date.today().year)

        # Generate the monthly report
        start_date = datetime.datetime(year, month, 1)
        end_date = datetime.datetime(year, month + 1, 1) if month < 12 else datetime.datetime(year + 1, 1, 1)

        report_data = db.products.find({
            "purchase_date": {"$gte": start_date, "$lt": end_date}
        })

        total_purchase_price = 0
        total_sales_price = 0

        # Store sales data for the report
        sales_report_data = []

        for product in report_data:
            total_purchase_price += product['quantity'] * product['price']
            total_sales_price += product['quantity'] * product['price']  # Assuming this is the sales price calculation

            # Append sales data for the report
            sales_report_data.append({
                "Product Name": product["name"],
                "Purchase Quantity": product["quantity"],
                "Purchase Price": product["price"],
                "Sales Date": product['purchase_date'],
                "Sales Price": product['quantity'] * product['price'],
                "Purchase Date": product['purchase_date'],
            })

        st.subheader("Monthly Purchase Price:")
        st.write(f"₹{total_purchase_price:.2f}")

        st.subheader("Monthly Sales Price:")
        st.write(f"₹{total_sales_price:.2f}")

        st.subheader("Monthly Profit:")
        monthly_profit = total_sales_price - total_purchase_price
        st.write(f"₹{monthly_profit:.2f}")

        # Display the sales data in a table
        if sales_report_data:
            st.subheader("Monthly Sales Report")
            st.table(pd.DataFrame(sales_report_data))

# Run the app
if __name__ == "__main__":
    if not login:
        st.write("Please log in to access the app.")
