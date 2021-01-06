import pandas as pd
import psycopg2
import streamlit as st
from configparser import ConfigParser

st.title('Trader Management System')

@st.cache
def get_config(filename='database.ini', section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)
    return {k: v for k, v in parser.items(section)}
	
def query_db(sql: str):
	# print(f'Running query_db(): {sql}')
	
	db_info = get_config()
	
	# Connect to an existing database
	conn = psycopg2.connect(**db_info)
	
	# Open a cursor to perform database operations
	cur = conn.cursor()
	
	# Execute a command: this creates a new table
	cur.execute(sql)
	
	# Obtain data
	data = cur.fetchall()
	column_names = [desc[0] for desc in cur.description]
	
	# Make the changes to the database persistent
	conn.commit()
	
	# Close communication with the database
	cur.close()
	conn.close()
	
	df = pd.DataFrame(data=data, columns=column_names)

	return df
	

def alter_db(sql: str):
    # print(f'Running query_db(): {sql}')
 
    db_info = get_config()
 
    # Connect to an existing database
    conn = psycopg2.connect(**db_info)
	
 
    # Open a cursor to perform database operations
    cur = conn.cursor()
 
    # Execute a command: this creates a new table
    cur.execute(sql)
	
    # Make the changes to the database persistent
    conn.commit()
 
    # Close communication with the database
    cur.close()
    conn.close()

def calc_total_balance(user_id):
	sql_totalcash = f"""select distinct on (uid) uid, sum(balance) as sm
						from own_accounts
						where uid = '{user_id}'
						group by uid
						order by uid"""
	
	totalcash = query_db(sql_totalcash)
	totalsum = 0
	totalcash_sum = totalcash['sm'].tolist()
	for i in range(len(totalcash_sum)):
		totalsum += totalcash['sm'][i]
	return totalsum

def current_portfolio(user_id):
	sql_portfolio = f"""select r.ticker, sum(r.nshares) as total
						from records r, 
							(select r.ticker, r.uid 
							 from records r 
							 where r.buysell = True 
							 except
							 select r.ticker, r.uid 
							 from records r 
							 where r.buysell = False) as lp 
						where lp.ticker = r.ticker and lp.uid = r.uid and r.uid = '{user_id}'
						group by r.ticker
						union
						select r.ticker, sum(case when r.buysell = TRUE then r.nshares end) - sum(case when r.buysell = FALSE then r.nshares end)
						from records r
						where r.uid = '{user_id}'
						group by r.ticker
						having sum(case when r.buysell = TRUE then r.nshares end) - sum(case when r.buysell = FALSE then r.nshares end) > 0;"""					
	portfolio = query_db(sql_portfolio)
	return portfolio
###################################################################################################
################################ User Information #################################################
###################################################################################################
#Get Text input from user to login
name_text = st.sidebar.text_input("Enter Your Name")
password_text = st.sidebar.text_input("Enter Your Password",type='password')
sql_users = f"select id from users where name = '{name_text}' and password = '{password_text}';"
user_query = query_db(sql_users)['id'].tolist()

#Log in to get current user information
if st.sidebar.checkbox("Log In"):
	if user_query:
		st.subheader("Your Information")
		user_id = user_query[0]
		sql_user_info = f"select * from users where users.id = {user_id}"
		user_info = query_db(sql_user_info)
		
		########################### User Profile Information ###############################
		st.subheader("Profile Information")
		
		#User name
		user_info_name = user_info['name'].loc[0]
		st.write(f"Your ID: {user_id}")
		
		#User Business
		user_info_workplace = user_info['workplace'].loc[0]
		st.write(f"Your Workplace: {user_info_workplace}")
		
		if st.checkbox("Edit Business"):
			sql_user_business = "select name from businesses;"
			user_business = query_db(sql_user_business)['name'].tolist()
			
			user_business_selectbox = st.selectbox("Do you belong to any of these businesses?", user_business)
			new_business_checkbox = st.checkbox("Didn't find your business?")
			
			if new_business_checkbox:
				new_business_name = st.text_input("Enter the name of the business")
				new_business_year = st.number_input("Enter the year the business was founded")
				
			if st.button("Update business"):
				if new_business_checkbox:
					if new_business_name and new_business_year:
						add_to_businesses = f"""insert into businesses(name, year) values ('{new_business_name}', {new_business_year});"""
						update_user_business = f"""update users set workplace = '{new_business_name}' where users.id = {user_id};"""
						alter_db(add_to_businesses)
						alter_db(update_user_business)
						st.success("Workplace Successfully Changed")
						
					else:
						st.warning("Must enter both the name and the year, or uncheck the new business option")
						
				else:
					update_user_business = f"""update users set workplace = '{user_business_selectbox}' where users.id = {user_id};"""
					alter_db(update_user_business)
					st.success("Workplace Successfully Changed")
			
		
		#User Region
		user_info_region = user_info['region_in'].loc[0]
		st.write(f"Region you live in: {user_info_region}")
		if st.checkbox("Edit Region"):
		
			#make selectbox of regions(no others will be added)
			sql_user_region = f"select name from regions;"
			user_region = query_db(sql_user_region)['name'].tolist()
			user_region_select = st.selectbox("Which region do you live in?", user_region)
			
			#Update user's region_of value to the selected region
			if st.button("Confirm Region"):
				sql_user_region_change = f"""update users set region_in = '{user_region_select}' where users.id = {user_id};"""
				user_region_change = alter_db(sql_user_region_change)
				st.success("Region Successfully Changed")
		
		
		############################## User Buy/Sell Stocks ######################################
		st.subheader("Buy/Sell Stocks")
		
		#User adds a record (buys/sells a stock)
		if st.checkbox("Buy/Sell stocks"):
		
			#Get Account Information
			sql_get_accounts = f"""select id, balance from own_accounts where own_accounts.uid = {user_id};"""
			get_accounts = query_db(sql_get_accounts)
			get_accounts_id = get_accounts['id'].tolist()
			get_accounts_balance = get_accounts['balance'].tolist()
			if get_accounts_id:
				st.dataframe(get_accounts)
				
				#Combine account id and balance into string "id:balance"
				get_accounts_idbalance = []
				for i in range(len(get_accounts_id)):
					get_accounts_idbalance.append(f"{get_accounts_id[i]}:{get_accounts_balance[i]}")
				
				#Choose account
				select_account = st.selectbox("Which account will you use?", get_accounts_idbalance)
				
				#Split id and balance
				buysell_account = select_account.split(':')
				buysell_account_id = int(buysell_account[0])
				if(buysell_account[1] == 'None'):
					buysell_balance = 0.0
				else:
					buysell_balance = float(buysell_account[1])
				st.write(f"Current Account Balance: {buysell_balance}")
				
				#Choose 'Buy' or 'Sell'
				choose_buysell = st.radio("Buying or Selling?", ['Buy', 'Sell'])
				if choose_buysell == 'Buy':
					#Make Selectbox to choose an exchange
					sql_buy_exchange = "select name from exchanges;"
					buy_exchange = query_db(sql_buy_exchange)['name'].tolist()
					buy_selectbox = st.selectbox("Choose An Exchange", buy_exchange)
					if st.checkbox("Choose Stock to Buy"):
						#Make selectbox to choose a stock
						sql_buy_stocks = f"select s.name, s.ticker from stocks s, exchanges e, traded_on t where s.ticker = t.sticker and t.ename = e.shortname and e.name = '{buy_selectbox}';"
						buy_stocks = query_db(sql_buy_stocks)['name'].tolist()
						buy_stocks_selectbox = st.selectbox("Choose A Stock", buy_stocks)
						platform_checkbox = st.checkbox("On A Platform?")
						if platform_checkbox:
							buy_platform = st.text_input("What is the platform called?")
						if st.checkbox("Choose Amount to Buy"):
							sql_buy_stocks_ticker = f"select ticker from stocks s where name = '{buy_stocks_selectbox}';"
							buy_stocks_ticker = query_db(sql_buy_stocks_ticker)['ticker'].loc[0]
							#make number inputs to choose buy information
							buy_amount = st.number_input("Enter a cost amount")
							buy_count = st.number_input("How many shares?")
							buy_count = int(buy_count)
							
							#Stocks are either too expensive, or a record is created
							if st.button("Buy"):
								if (buy_amount*buy_count) > buysell_balance:
									st.warning("You don't have enough money in this account")
								elif buy_amount and buy_count:
									if not platform_checkbox:
										sql_buy_insert = f"""insert into records(uid, buysell, cost, nshares, ticker) 
													values ({user_id}, TRUE, {buy_amount}, {buy_count}, '{buy_stocks_ticker}');"""
									else:
										sql_buy_insert = f"""insert into records(uid, buysell, cost, nshares, platform, ticker) 
																values ({user_id}, TRUE, {buy_amount}, {buy_count}, '{buy_platform}', '{buy_stocks_ticker}');"""
									alter_db(sql_buy_insert)
									new_balance = buysell_balance - (buy_amount*buy_count)
									sql_update_account = f"""update own_accounts set  balance = {new_balance} where own_accounts.id = {buysell_account_id};"""
									alter_db(sql_update_account)
									st.success("Stock Bought")
								else:
									st.warning("Must enter cost and number of shares")
				
				
				if choose_buysell == 'Sell':
					#Gather portfolio to find stocks owned
					"""Current Portfolio of stocks"""
					sell_portfolio = current_portfolio(user_id)
					st.dataframe(sell_portfolio)
					
					sell_stocks = sell_portfolio['ticker'].tolist()
					sell_stocks_nshares = sell_portfolio['total'].tolist()
					
					sell_stocks_selectbox = st.selectbox("Choose a stock to sell", sell_stocks)
					if st.checkbox("Choose Exchange to Sell On"):
					
						#Get information on stock chosen
						for i in range(len(sell_stocks)):
							if sell_stocks[i] == sell_stocks_selectbox:
								sold_stock = sell_stocks[i]
								sold_count = sell_stocks_nshares[i]
								break
						
						#Combine the stocks into a single string to use in the select statement
						sql_sell_exchanges = f"""select distinct e.name as exchange from exchanges e, stocks s, traded_on t
											where e.shortname = t.ename and t.sticker = '{sold_stock}';"""
						sell_exchanges = query_db(sql_sell_exchanges)['exchange'].tolist()
						sell_exchanges_selectbox = st.selectbox("Choose an Exchange to sell on", sell_exchanges)
						if st.checkbox("Choose Amount to Sell"):
							sell_amount = st.number_input("How much is it selling for?")
							sell_count = st.number_input("How many will you sell?")
							
							#Stocks are either not enough or a record is created
							if st.button("Sell"):
								if sell_count > sold_count:
									st.warning("Not enough shares to sell that much")
								else:
									sql_sell_insert = f"""insert into records(uid, buysell, cost, nshares, ticker)
														values ({user_id}, FALSE, {sell_amount}, {sell_count}, '{sell_stocks_selectbox}');"""
									alter_db(sql_sell_insert)
									new_balance = buysell_balance + (sell_count*sell_amount)
									sql_update_account = f"""update own_accounts set  balance = {new_balance} where own_accounts.id = {buysell_account_id};"""
									alter_db(sql_update_account)
									st.success("Stock Sold")
			else:
				st.warning("No account to use")
							
		############################## User Stock Information ######################################
		st.subheader("Stock Information")
		
		#Calculate realized profit/loss
		if st.button("Calculate Realized Profit"):
			
			#Select stocks that have been bought and then sold to calculate realized profit or loss
			sql_lossprofit = f"""select r.ticker, r.buysell, r.cost, r.nShares
								from records r,
									(select r.ticker, r.uid
									from records r
									where r.buysell = True
									Intersect
									Select r.ticker, r.uid
									from records r
									where r.buysell = False) as lp
								where lp.ticker = r.ticker and lp.uid = r.uid 
								and r.uid = '{user_id}'
								order by r.ticker, r.ttime asc, r.buysell desc;"""
			lossprofit = query_db(sql_lossprofit)
			lossprofit_buysell = lossprofit['buysell'].tolist()
			lossprofit_cost = lossprofit['cost'].tolist()
			lossprofit_nshares = lossprofit['nshares'].tolist()
			
			#Place the buy values into a stack, then pop each value when a stock is sold
			st.dataframe(lossprofit)
			shares_bought_values = []
			lossprofit_value = 0
			for i in range(len(lossprofit_buysell)):
				
				#Push buy values into stack
				if lossprofit_buysell[i] == 1:
					for j in range(lossprofit_nshares[i]):
						shares_bought_values.append(lossprofit_cost[i])
						
				#Pop buy values from stack to subtract from sell values
				else:
					for j in range(lossprofit_nshares[i]):
						temp_share = shares_bought_values.pop()
						lossprofit_value += lossprofit_cost[i] - temp_share	
			
			st.write(f"Realized Profit/Loss: {lossprofit_value}")


		#Display list of stocks the user currently holds (Their portfolio)
		if st.button("Display Current Portfolio"):

			portfolio = current_portfolio(user_id)
			"""Portfolio"""
			st.dataframe(portfolio)

		#Calculate total balances in accounts connected to the user id
		if st.button("Calculate Current Total Balance"):
			totalBalance = calc_total_balance(user_id)
			st.write(f"Current Total Balance: {totalBalance}")
			
		############################## Account Information ######################################
		st.subheader("Account Management")
		
		if st.checkbox("Add/Remove Account"):
			account_addrem_radio = st.radio("Add or Remove", ['Add','Remove'])
			
			if account_addrem_radio == 'Add':
			
				st.write("Are you sure you want to add and account?")
				if st.button("Yes, add an account"):
				
					add_an_account = f"""insert into own_accounts(uid) values ({user_id});"""
					alter_db(add_an_account)
					st.success("Successfully added an account")
					
					
			else:
				sql_remove_accounts = f"select id, balance from own_accounts a where a.uid = {user_id};"
				remove_accounts = query_db(sql_remove_accounts)
				remove_accounts_id = remove_accounts['id'].tolist()
				remove_accounts_balance = remove_accounts['balance'].tolist()
				
				if remove_accounts_id:
				
					remove_accounts_idbalance = []
					for i in range(len(remove_accounts_id)):
						remove_accounts_idbalance.append(f"{remove_accounts_id[i]}:{remove_accounts_balance[i]}")
						
					remove_accounts_selectbox = st.selectbox("Select an account to remove", remove_accounts_idbalance)
					if st.button("Remove account"):
					
						remove_accounts_split = remove_accounts_selectbox.split(':')
						remove_account_id = remove_accounts_split[0]
						
						sql_remove_account = f"""delete from own_accounts o where o.id = {remove_account_id};"""
						alter_db(sql_remove_account)
						st.success("Successfully deleted account")
				else:
					st.warning("No accounts to remove")
				
				
		if st.checkbox("Add Money to Account"):
		
			#select statement finds accounts
			sql_find_account = f"select id, balance from own_accounts a where a.uid = {user_id};"
			find_account = query_db(sql_find_account)
			find_account_id = find_account['id'].tolist()
			find_account_balance = find_account['balance'].tolist()
			if find_account_id:
			
				#Combine select results into a string 'id:balance'
				find_account_idbalance = []
				for i in range(len(find_account_id)):
					find_account_idbalance.append(f"{find_account_id[i]}:{find_account_balance[i]}")
				
				#Get inputs
				select_add_account = st.selectbox("Which account to add to?", find_account_idbalance)
				account_add_money = st.number_input("How Much?")
				
				#Adds money if both inputs exist
				if st.button("Add Money"):
					if account_add_money and select_add_account:
						
						#Split the 'id:balance' string
						add_account_split = select_add_account.split(':')
						add_account_id = int(add_account_split[0])
						add_account_balance = add_account_split[1]
						
						#Calculate the new balance
						new_account_balance = float(add_account_balance) + account_add_money
						
						#Change the balance
						sql_adding_money = f"""update own_accounts set balance = {new_account_balance} where own_accounts.id = {add_account_id};"""
						alter_db(sql_adding_money)
						st.success("Successfully Added Money")
					else:
						st.warning("Need to enter an amount or choose an account")
			else:
				st.warning("No account to add to")
		
		
		################################ User Friend Information #################################
		st.subheader("Friend Section")
		
		#Display user's friends
		"""Your Friends"""
		sql_friends = f"""select f.fname from friends_of f where f.uid = {user_id};"""
		friends = query_db(sql_friends)
		st.dataframe(friends)
		
		#Display Friends' most recent activity
		"""Your friends' most recent activity"""
		sql_friend_activity = f"""select distinct f.fname as Friend, rt.ttime as Recent_Activity
							from friends_of f,
								(select distinct on (r.uid) r.uid, r.ttime
								from records r
								group by r.uid, r.ttime
								order by r.uid, r.ttime desc) as rt
							where f.uid = {user_id} and f.fid = rt.uid;"""
		friend_activity = query_db(sql_friend_activity)
		st.dataframe(friend_activity)
		
		
		#Add a friend
		if st.checkbox("Add a friend?"):
		
			#Input friend id
			st.write("Search for a friend using their ID")
			new_friend_id_str = st.text_input("Enter An ID")
			if st.checkbox("Search"):
			
				#Make sure an id was inputted
				if new_friend_id_str:
					new_friend_id = int(new_friend_id_str)
					
					#Check to make sure the id exists
					sql_search_new_friend = f"""select name from users where users.id = {new_friend_id};"""
					search_new_friend = query_db(sql_search_new_friend)['name'].tolist()
					if search_new_friend:
						new_friend_name = search_new_friend[0]
						st.write(f"We found {new_friend_name}, is this who you were looking for?")
						
						#Insert friend into friends_of database
						if st.button("Yes, Add Friend"):
							add_new_friend = f"""insert into friends_of(uid, fid, fname) values ({user_id},{new_friend_id},'{new_friend_name}');"""
							alter_db(add_new_friend)
							st.success("Successfully added a friend")
					else:
						st.warning("Must enter a valid ID")

				else:
					st.warning("Must enter an ID")
		
		
		#Delete a Friend
		if st.checkbox("Remove a friend?"):
			#Collect the list of user's friends
			sql_remove_friend_list = f"select fid, fname from friends_of f where f.uid = {user_id};"
			remove_friend_list = query_db(sql_remove_friend_list)
			remove_friend_ids = remove_friend_list['fid'].tolist()
			remove_friend_names = remove_friend_list['fname'].tolist()
			
			#Combine fid and fname into a string 'fid:fname'
			combined_friend_idnames = []
			for i in range(len(remove_friend_ids)):
				combined_friend_idnames.append(f"{remove_friend_ids[i]}:{remove_friend_names[i]}")
			
			#multiselect button
			remove_friend_multiselect = st.multiselect("Choose friends to remove", combined_friend_idnames)
			if remove_friend_multiselect:

				#split 'id:name' apart to retrieve the id
				remove_friend_id_split = []
				for i in range(len(remove_friend_multiselect)):
					remove_friend_id_split.append(remove_friend_multiselect[i].split(":")[0])
					remove_friend_id_split[i] = int(remove_friend_id_split[i])
					
				st.write(f"Are you sure you want to delete {remove_friend_multiselect} from your friend list?")
				
				#removing list of friends from friends database
				if st.button("Yes, Delete These Friends"):
					remove_friend_id_join = ",".join(str(elem) for elem in remove_friend_id_split)
					sql_removing_friends = f"""delete from friends_of f where f.uid = {user_id} and f.fid in ({remove_friend_id_join});"""
					alter_db(sql_removing_friends)
					st.success("Successfully removed friend(s)")
				
			
	else:
		st.warning("Incorrect Username or Password")
		
#create new user with name and password to be added to the database
if st.sidebar.button("Sign Up"):
	if user_query:
		st.warning("Username and Password already in use")
		
	else:
		insert_new_user = f"insert into users(name, password) values ('{name_text}', '{password_text}');"
		insert_user = alter_db(insert_new_user)
		st.success("Successfully signed up")

###################################################################################################
############################# General Information #################################################
###################################################################################################
st.subheader("General Information")

#Use a multiselect box to display stocks traded in chosen regions
sql_regions = 'select name from regions;'
region_names = query_db(sql_regions)['name'].tolist()
region_select = st.multiselect("Choose a region", region_names)
if region_select:
	region_join = "','".join(elem for elem in region_select)
	region_join = "'" + region_join + "'"
	
	sql_regions_trading = f"""select r.name as region, s.name as stock_name, s.ticker as stock_ticker
							from regions r, stocks s, traded_on t, exchanges e
							where s.ticker = t.sTicker 
							and t.ename = e.shortname and e.region = r.name 
							and r.name in ({region_join})
							group by s.ticker, s.name, r.name
							order by s.ticker, s.name, r.name;"""

	regions_trading = query_db(sql_regions_trading)
	st.write(f"stocks traded in {region_select}")
	st.dataframe(regions_trading)
	
#Most traded stock per region
if st.checkbox("Most traded stock per region"):
	sql_most_traded = f"""select distinct on (e.region) e.region, s.name, s.ticker
						from stocks s, exchanges e, traded_on t,
							(select re.ticker, count(re.ticker) as cnt
							 from records re
							 group by re.ticker
							 order by cnt) as freq
						where t.ename = e.shortname and t.sticker = s.ticker
						and e.region != '' and freq.ticker = s.ticker
						group by e.region, s.name, s.ticker, freq.cnt
						order by e.region, freq.cnt desc;"""
	most_traded = query_db(sql_most_traded)
	st.dataframe(most_traded)


#Use a selectbox to display stocks traded in a specific stock exchange
sql_exchanges = 'select name from exchanges;'
exchange_names = query_db(sql_exchanges)['name'].tolist()
exchange_select = st.selectbox("Choose an exchange", exchange_names)
exchange_button = st.button("Find Stocks", exchange_select)
if exchange_button:
	sql_exchanges_trading = f"""select s.ticker as Ticker, s.name as Stock_Name, e.shortname as Exchange_Shortname,  e.name as Exchange
							from stocks s, traded_on t, exchanges e
							where s.ticker = t.sTicker 
							and t.ename = e.shortname and e.name = '{exchange_select}'"""

	exchanges_trading = query_db(sql_exchanges_trading)
	st.write(f"stocks traded in {exchange_select}")
	st.dataframe(exchanges_trading)


"""Business info based on Traders"""
#Display businesses ordered by the number of traders they employ
if st.button("Display businesses ordered by the number of traders they employ"):
	sql_businesses = """select B.name, count(U.id)
						from businesses B, Users U
						where U.workplace = B.name
						group by B.name
						order by count(U.id) desc;"""
						
	"""Business Ordered By Number of Traders Employed"""
	businesses = query_db(sql_businesses)
	st.dataframe(businesses)

#Display businesses ordered by the number of traders they employ that own their stock
if st.button("Display businesses ordered by the number of traders they employ that own their stock"):
	sql_business_stock = """select distinct s.business, count(freq.uid) as employees
							from stocks s, users u,
								(select r.ticker, r.uid 
								from records r,
									(select r.ticker, r.uid 
									from records r 
									where r.buysell = True 
									except 
									select r.ticker, r.uid 
									from records r 
									where r.buysell = False) as lp 
								where lp.ticker = r.ticker and lp.uid = r.uid
								union
								select r.ticker, r.uid 
								from records r, records l
								where r.buysell = True and l.buysell = False
								and r.ticker = l.ticker and r.uid = l.uid) as freq
							where s.ticker = freq.ticker and freq.uid = u.id and u.workplace = s.business
							group by s.business
							order by count(freq.uid) desc;"""
							
	"""Businesses Ordered By Number of Trader Employees That Own Their Stock"""
	business_stock = query_db(sql_business_stock)
	st.dataframe(business_stock)