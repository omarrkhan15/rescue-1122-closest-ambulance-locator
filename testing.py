from groq import Groq

client = Groq(api_key="")

def call_llm(prompt):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


def main():
    address_text = "my house is near checkpost 5 malir cantt, it is inside malir cantt,askari 5 is inside malir cantt and the building is 106 which is inside askari5 which is inside malir"
    landmark_text = "checkpost 5"

    prompt = f"""
Extract the clean physical address from this text.
it should be in a format that my geopy python library can understand.
Return ONLY the address, nothing else. the format for geopy should be like first smaller address then larger like house num then area then city etc

Address: {address_text}
Landmark: {landmark_text}
"""

    cleaned_address = call_llm(prompt)
    print(f"Cleaned Address: {cleaned_address}")


if __name__ == "__main__":
    main()
