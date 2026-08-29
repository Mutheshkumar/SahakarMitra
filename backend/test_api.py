import requests
import json

API_URL = "http://localhost:8000/ask"

questions = [
    "What is the ultimate authority of a registered society and when should a general meeting be convened?",
    "Who conducts the election of the board and what is the term length?",
    "How often should the accounts be audited?",
    "Under what conditions can a member be expelled?",
    "Who has the authority to issue an order to wind up a society?",
    "What happens if I try to start a bank?", # Should not be covered
]

def main():
    for q in questions:
        print(f"\n{'-'*50}")
        print(f"QUESTION: {q}")
        
        payload = {"question": q}
        try:
            response = requests.post(API_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            
            print(f"ANSWER: {data['answer']}")
            print(f"CITED SECTION: {data.get('cited_section')}")
            
            # Print retrieved sections briefly
            retrieved = [f"Sec {s['section']} ({s['title']})" for s in data.get('retrieved_sections', [])]
            print(f"RETRIEVED: {', '.join(retrieved)}")
            
        except requests.exceptions.RequestException as e:
            print(f"Error calling API: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Details: {e.response.text}")

if __name__ == "__main__":
    main()
