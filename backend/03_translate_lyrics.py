#!/usr/bin/env python3
import argparse
import json
import os
import sys  # for sys.exit

# Import LangChain and OpenAI related libraries
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


def translate_lyrics(input_file_path: str, output_file_path: str | None):
    """
    Reads a Japanese lyrics JSON file, translates it into English, and saves it to a new JSON file.

    Args:
        input_file_path (str): Path to the input JSON file.
        output_file_path (str): Path to the output JSON file.
    """
    # 1. Check OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key is None:
        print("Error: Environment variable OPENAI_API_KEY is not set.")
        print("Please set OPENAI_API_KEY before running the script.")
        print("Example: export OPENAI_API_KEY='your_api_key_here'")
        return

    # 2. Read input file
    try:
        with open(input_file_path, "r", encoding="utf-8") as f:
            lyrics_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file_path}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Input file '{input_file_path}' is not a valid JSON format.")
        return
    except Exception as e:
        print(
            f"An unexpected error occurred while reading input file '{input_file_path}': {e}"
        )
        return

    # Check input data format
    if not isinstance(lyrics_data, list):
        print(f"Error: The content of input file '{input_file_path}' must be a list.")
        return
    if not all(
        isinstance(item, dict) and "text" in item and "start" in item and "end" in item
        for item in lyrics_data
    ):
        print(
            f"Error: Each element in the input file must be a dictionary with 'text', 'start', and 'end' keys."
        )
        return

    # If output file path is not specified, save in the same directory as the input file
    if output_file_path is None:
        output_file_path = os.path.splitext(input_file_path)[0] + "_translated.json"

    japanese_texts = [item["text"] for item in lyrics_data]
    num_original_lines = len(japanese_texts)
    japanese_lyrics_block = "\n".join(japanese_texts)

    # 3. Create prompt
    # Hint: Include the entire lyrics in the prompt and specify the output format in the prompt
    #       to make it easier to extract the English lyrics accurately.
    prompt_template_str = """\
以下の日本語の歌詞を英語に翻訳してください。
各行の翻訳は改行で区切って、元の歌詞の行数と全く同じ数の翻訳行を生成してください。
翻訳は自然で、歌詞としての流れを意識してください。

# 歌詞

<lyrics>
{lyrics}
</lyrics>

# 条件

* もとの歌詞の意味合いと雰囲気を可能な限り維持してください
* 翻訳された各行は、元の日本語の歌詞の各行に厳密に対応する必要があります。
* 空の行や不必要な空白行を生成しないでください。元の行数と完全に一致させてください。
* もとの歌詞と翻訳結果以外は一切出力しないでください。
* 前置き、後書き、元の日本語歌詞、追加のコメントや説明は一切含めないでください。
* 下記の出力形式に厳密に従ってください。

# 出力形式

```
[日本語歌詞の1行目],[1行目の翻訳結果]
[日本語歌詞の2行目],[2行目の翻訳結果]
(以降同様に続く)
```
"""

    current_temperature = 0.0
    # Hint: If the output does not follow the instructions, increase the value of temperature by 0.2
    #       and retry translation until the correct result is obtained.
    #       Here, try up to a maximum of 1.0.
    max_temperature = 1.0
    temperature_step = 0.2
    translated_lines_list: list[str] = []

    print(f"Starting translation. Number of input lines: {num_original_lines}")

    # 4. Translation using ChatOpenAI (including retry logic)
    while current_temperature <= max_temperature:
        print(f"  Trying translation with temperature {current_temperature:.1f}...")

        # Initialize ChatOpenAI
        # Condition: Set temperature parameter of ChatOpenAI to 0 and seed to 42.
        # (First try with temperature=0, increase temperature on retry)
        chat_model = ChatOpenAI(
            temperature=current_temperature,
            name="gpt-4.1-mini",
            timeout=120,  # Set a longer timeout
            seed=42,  # Seed value to improve reproducibility of model output
        )

        prompt = ChatPromptTemplate.from_template(prompt_template_str)
        chain = prompt | chat_model | StrOutputParser()

        # To maintain consistency of lyrics, call ChatOpenAI once for the whole lyrics, not line by line
        response_text = chain.invoke({"lyrics": japanese_lyrics_block})
        response_text = response_text.replace("```", "")

        # Parse and validate translation result
        # Remove leading/trailing whitespace/newlines with strip(), then split by newline
        potential_translations = response_text.strip().split("\n")
        # Further strip each line
        potential_translations = [line.strip() for line in potential_translations]
        # Skip empty lines
        potential_translations = [line for line in potential_translations if line]
        # Split each line by comma and extract the translation part
        potential_translations = [
            ",".join(line.split(",")[1:]).strip() for line in potential_translations
        ]

        # If the number of lines matches, break the loop
        if len(potential_translations) == num_original_lines:
            translated_lines_list = potential_translations
            break

        # If the number of lines does not match, increase temperature and retry
        print(
            f"  The number of lines in the translation result with temperature {current_temperature:.1f} did not match."
        )
        print(
            f"    Expected lines: {num_original_lines}, Actual lines: {len(potential_translations)}"
        )

        current_temperature += temperature_step
        # Small value for floating point comparison
        if (
            current_temperature > max_temperature + 1e-9
            and translated_lines_list is None
        ):
            print(f"  Reached maximum temperature ({max_temperature:.1f}).")
            break

    if not translated_lines_list:
        raise RuntimeError(
            "Warning: Translation failed for all temperature settings or the result was not in the expected format."
        )

    # 5. Create output data
    for i, item in enumerate(lyrics_data):
        # Condition: For each dictionary, add a new key "translations",
        #            and create a nested key "en" inside it
        if "translations" not in item:
            item["translations"] = {}
        item["translations"]["en"] = translated_lines_list[i]
    print("Incorporated translation results into output data.")

    # 6. Save output file
    # Condition: Save the output result in JSON format to a path different from the input file
    try:
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(lyrics_data, f, ensure_ascii=False, indent=4)
        print(f"Saved translation result to '{output_file_path}'.")
    except Exception as e:
        print(
            f"An error occurred while saving to output file '{output_file_path}': {e}"
        )


def main():
    # Load environment variables
    load_dotenv()

    # Set up command line arguments
    parser = argparse.ArgumentParser(
        description="Translates a JSON file containing Japanese lyrics into English and outputs the result to another JSON file.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "input_file",
        help="Path to the input JSON file.\n"
        "Each element must be in the form {'text': str, 'start': float, 'end': float}.",
    )
    parser.add_argument(
        "--output_file",
        default=None,
        help="Path to the output JSON file.\n"
        "The input data with translation results added will be saved here.",
    )

    args = parser.parse_args()
    if args.output_file is None:
        args.output_file = os.path.splitext(args.input_file)[0] + "_translated.json"

    translate_lyrics(args.input_file, args.output_file)


if __name__ == "__main__":
    # --- Usage ---
    # 1. Set your OpenAI API key as an environment variable:
    #    export OPENAI_API_KEY="sk-..."
    #
    # 2. Run the script:
    #    python your_script_name.py input_lyrics.json output_translated_lyrics.json
    #
    #    Example:
    #    Input file (input_lyrics.json):
    #    [
    #        {"text": "こんにちは世界", "start": 0.0, "end": 2.0},
    #        {"text": "ありがとう", "start": 2.5, "end": 4.0}
    #    ]
    #
    #    Expected format of output file (output_translated_lyrics.json):
    #    [
    #        {
    #            "text": "こんにちは世界", "start": 0.0, "end": 2.0,
    #            "translations": {"en": "Hello world"}
    #        },
    #        {
    #            "text": "ありがとう", "start": 2.5, "end": 4.0,
    #            "translations": {"en": "Thank you"}
    #        }
    #    ]
    # (Actual translation content depends on the model)
    # -----------------
    main()
