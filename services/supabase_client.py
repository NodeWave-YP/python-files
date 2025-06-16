from supabase import Client, create_client
from decouple import config


url = config("SUPABASE_URL")
key = config("SUPABASE_KEY")


supabase: Client = create_client(url, key)