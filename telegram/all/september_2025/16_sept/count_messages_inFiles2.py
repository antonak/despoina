import json
import sys

def count_messages(filenames):
    """Count the number of messages in the specified JSON files."""
    total_count = 0

    for filename in filenames:
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Assuming data is a list of messages
            message_count = len(data)
            total_count += message_count

            # Print the message count for the current file
            print(f"Total number of messages in '{filename}': {message_count}")
        
        except FileNotFoundError:
            print(f"Error: The file '{filename}' was not found.")
        except json.JSONDecodeError:
            print(f"Error: The file '{filename}' is not a valid JSON file.")
        except Exception as e:
            print(f"An error occurred while processing '{filename}': {e}")

    # Print the total message count across all files
    print(f"\nTotal number of messages across all files: {total_count}")

if __name__ == "__main__":
    # Check if at least one filename was provided as a command line argument
    if len(sys.argv) < 2:
        print("Usage: python count_messages.py <filename1> <filename2> ... <filenameN>")
        sys.exit(1)

    # Get the filenames from command line arguments
    filenames = sys.argv[1:]
    
    # Count messages in the provided JSON files
    count_messages(filenames)

