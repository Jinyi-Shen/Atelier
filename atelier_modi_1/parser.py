import re

def parse_input_file(file_path):
    while True:
        try:
            # 尝试打开并读取文件内容
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()

            # 使用正则表达式匹配键和值
            pattern = r"\[(.*?)\]:\s*\{\{(.*?)\}\}"
            matches = re.findall(pattern, text, re.DOTALL)

            # 创建字典存储结果
            result_dict = {}
            for key, value in matches:
                cleaned_key = key.strip()
                cleaned_value = value.strip()
                result_dict[cleaned_key] = cleaned_value

            return result_dict
        except FileNotFoundError:
            # 如果指定的文件不存在，则提示用户并继续循环
            print("File not found. Please try again.")
        except Exception as e:
            # 处理其他可能的异常，如权限问题等
            print(f"An error occurred: {e}")
            break  # 通常在未知错误发生时终止循环
def write_text_to_file(file_path, text:dict, title):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(title + '\n')
        for key,value in text.items():
            file.write(f"[{key}]: {{{value}}}\n")
    return

if __name__ == "__main__":
    # 使用示例
    if True:
        text1 = {
            "circuit_name": "My Circuit",
            "desired_metrics": "Low THD, High SNR",
            "initial_metrics": "THD: 0.1%, SNR: 90dB"
        }
        text2 = {
            "circuit_name": "Another Circuit",
            "desired_metrics": "High Bandwidth",
            "initial_metrics": "Bandwidth: 1MHz"
        }
        file_location = "output.txt"
        write_text_to_file(file_location, text1, "Circuit Information")
        write_text_to_file(file_location, text2, "Additional Information")
    if False:
        inputs = parse_input_file()
        for key in inputs:
            if key == "circuit_name":
                circuit_name = inputs[key]
            elif key == "desired_metrics":
                desired_metrics = inputs[key]
            elif key == "initial_metrics":
                initial_metrics = inputs[key]
        print(f"Circuit Name: {circuit_name}, Desired Metrics: {desired_metrics}, Initial Metrics: {initial_metrics}")
