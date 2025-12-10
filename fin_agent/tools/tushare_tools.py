import tushare as ts
import pandas as pd
from fin_agent.config import Config
import json
from datetime import datetime, timedelta

# Initialize Tushare - will be re-initialized when called if Config updates
def get_pro():
    ts.set_token(Config.TUSHARE_TOKEN)
    return ts.pro_api()

def get_current_time():
    """Get current date and time."""
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_stock_basic(ts_code=None, name=None):
    """
    Get basic stock information.
    :param ts_code: Stock code (e.g., 000001.SZ)
    :param name: Stock name (e.g., 平安银行)
    :return: DataFrame or dict string
    """
    try:
        pro = get_pro()
        # If name is provided but ts_code is not, try to find ts_code
        if name and not ts_code:
            # Getting all stocks and filtering might be slow, but it's a simple way
            df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
            df = df[df['name'] == name]
            if df.empty:
                return f"Error: Stock with name '{name}' not found."
            return df.to_json(orient='records', force_ascii=False)
        
        # Otherwise use ts_code or just list all (limit to some reasonable amount if needed, but pro.stock_basic returns all usually)
        # To be safe for LLM, usually we query by specific code or just return error if both missing
        if not ts_code:
             return "Error: Please provide either ts_code or name."

        df = pro.stock_basic(ts_code=ts_code, fields='ts_code,symbol,name,area,industry,list_date')
        if df.empty:
            return f"Error: Stock code '{ts_code}' not found."
        return df.to_json(orient='records', force_ascii=False)
    except Exception as e:
        return f"Error fetching stock basic info: {str(e)}"

def get_daily_price(ts_code, start_date=None, end_date=None):
    """
    Get daily stock price.
    :param ts_code: Stock code
    :param start_date: Start date (YYYYMMDD)
    :param end_date: End date (YYYYMMDD)
    :return: JSON string
    """
    if not start_date:
        # Default to last 30 days
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y%m%d')

    try:
        pro = get_pro()
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if df.empty:
            return f"No data found for {ts_code} between {start_date} and {end_date}."
        
        # Ensure data is sorted by date descending
        df = df.sort_values('trade_date', ascending=False)
        return df.to_json(orient='records', force_ascii=False)
    except Exception as e:
        return f"Error fetching daily price: {str(e)}"

def get_realtime_price(ts_code):
    """
    Get realtime stock price using legacy Tushare interface.
    :param ts_code: Stock code (e.g., 000001.SZ -> 000001 for legacy)
    :return: JSON string
    """
    try:
        # Legacy interface takes code without suffix usually, but let's check input
        code = ts_code.split('.')[0] if '.' in ts_code else ts_code
        
        df = ts.get_realtime_quotes(code)
        if df is None or df.empty:
            return f"No realtime data found for {ts_code}."
            
        # Add ts_code back for clarity
        df['ts_code'] = ts_code
        return df.to_json(orient='records', force_ascii=False)
    except Exception as e:
        return f"Error fetching realtime price: {str(e)}"

def get_daily_basic(ts_code, start_date=None, end_date=None):
    """
    Get daily basic indicators (PE, PB, turnover, etc.).
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y%m%d')
        
    try:
        pro = get_pro()
        df = pro.daily_basic(ts_code=ts_code, start_date=start_date, end_date=end_date, 
                            fields='ts_code,trade_date,close,turnover_rate,volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,total_share,float_share,free_share,total_mv,circ_mv')
        if df.empty:
             return f"No daily basic data found for {ts_code}."
        df = df.sort_values('trade_date', ascending=False)
        return df.to_json(orient='records', force_ascii=False)
    except Exception as e:
        return f"Error fetching daily basic info: {str(e)}"

def get_income_statement(ts_code, start_date=None, end_date=None):
    """
    Get income statement data (Revenue, Profit).
    """
    if not start_date:
        # Last 2 years
        start_date = (datetime.now() - timedelta(days=730)).strftime('%Y%m%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y%m%d')
        
    try:
        pro = get_pro()
        df = pro.income(ts_code=ts_code, start_date=start_date, end_date=end_date,
                       fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,total_revenue,revenue,total_profit,n_income,n_income_attr_p')
        if df.empty:
            return f"No income statement data found for {ts_code}."
        df = df.sort_values('end_date', ascending=False)
        return df.to_json(orient='records', force_ascii=False)
    except Exception as e:
        return f"Error fetching income statement: {str(e)}"

# Tool definitions for LLM
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current system date and time. Use this when the user asks about 'today', 'now', or relative dates.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_basic",
            "description": "Get basic information about a stock, such as its industry, area, and listing date. You can search by stock name or code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ts_code": {
                        "type": "string",
                        "description": "The stock code (e.g., '000001.SZ')."
                    },
                    "name": {
                        "type": "string",
                        "description": "The stock name (e.g., '平安银行')."
                    }
                },
                "required": [] 
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_daily_price",
            "description": "Get historical daily price data for a stock within a date range (Open, High, Low, Close, Vol).",
            "parameters": {
                "type": "object",
                "properties": {
                    "ts_code": {
                        "type": "string",
                        "description": "The stock code (e.g., '000001.SZ')."
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYYMMDD format. Defaults to 30 days ago."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYYMMDD format. Defaults to today."
                    }
                },
                "required": ["ts_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_realtime_price",
            "description": "Get the latest real-time stock price data (current price, bid/ask, volume, etc.). Use this for the most up-to-date market snapshot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ts_code": {
                        "type": "string",
                        "description": "The stock code (e.g., '000001.SZ')."
                    }
                },
                "required": ["ts_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_daily_basic",
            "description": "Get daily basic indicators including PE (Price-to-Earnings), PB (Price-to-Book), Turnover Rate, and Market Value.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ts_code": {
                        "type": "string",
                        "description": "The stock code (e.g., '000001.SZ')."
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date (YYYYMMDD)."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date (YYYYMMDD)."
                    }
                },
                "required": ["ts_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_income_statement",
            "description": "Get historical income statement data (Revenue, Net Income) to analyze financial performance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ts_code": {
                        "type": "string",
                        "description": "The stock code (e.g., '000001.SZ')."
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date (YYYYMMDD). Defaults to 2 years ago."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date (YYYYMMDD)."
                    }
                },
                "required": ["ts_code"]
            }
        }
    }
]

# Helper to execute tool calls
def execute_tool_call(tool_name, arguments):
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            return "Error: Invalid JSON arguments."

    if tool_name == "get_current_time":
        return get_current_time()
    elif tool_name == "get_stock_basic":
        return get_stock_basic(**arguments)
    elif tool_name == "get_daily_price":
        return get_daily_price(**arguments)
    elif tool_name == "get_realtime_price":
        return get_realtime_price(**arguments)
    elif tool_name == "get_daily_basic":
        return get_daily_basic(**arguments)
    elif tool_name == "get_income_statement":
        return get_income_statement(**arguments)
    else:
        return f"Error: Tool '{tool_name}' not found."
