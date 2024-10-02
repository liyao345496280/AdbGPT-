import os
from loguru import logger
import uiautomator2 as u2
import time

from extract_step import Extract_Steps
from guided_replay import UI
from guided_replay import Guided_Replay
import adb
# -*- coding: gbk -*-
#### VERY IMPORTANT: Change the xml_screen_size in config to your device size

if __name__ == '__main__':
    save_path = "test"
    logger.add(os.path.join(save_path, "loguru.log"))

    with open('mid_result/html_code.txt', 'w', encoding='utf-8') as file_:
        pass

    with open('promt_text/extract_prompt.txt', 'r', encoding='utf-8') as file:
        ex_prompts = file.read()

    bug_description = """1. Go to Messaging\n2. Create a new conversation\n3. create a name with '123' \n4. Tap this conversation \n5. input 'LY' \n 6. Send Message\n 7. Return to previous screen """
    # bug_description = """1. Go to Messaging\n2. Long tap the '123'\n3. click delete and tap Sure"""
    # bug_description = """1. Open F-Droid\n2. Click "Settings" tab\n3. Scroll down to "Display" section\n4. click on "Theme"\n5. With the theme selector open (you can see choices like "Light", "Dark", "Night") tilt the device to change the orientation. If device did not crash yet, tilt it back to change orientation back."""
    # bug_description = """1. Open ATimeTracker,then make sound is enabled in Settings of ATimeTracker.\n2. Go to Android main view/screen (i.e. making sure ATimeTracker is not in the foreground).\n3. Start ATimeTracker.\n4. Start or stop an existing activity"""
    # bug_description = """1. Open AnkiDroid\n2. Press on + and choose Add card\n3. Press on attach and choose Add image\n4. Select Camera\n5. go to home"""
    # bug_description = """1. Open Messaging\n2. click more ,then Go to Setting\n3. click Advance \n4. tap phone number"""

    bug = bug_description
    question_prompt = """Question: Extract the entity from the following -> "{}"\n Answer: """.format(bug)
    prompt = ex_prompts + question_prompt
    prompt = prompt.strip()

    es = Extract_Steps()
    step_outputs = es.infer(prompt)
    with open('mid_result/step_outputs.txt', 'w', encoding='utf-8') as file:
        for step_output in step_outputs:
            file.write(f"{step_output.step_text}\n")

    d = u2.connect()
    print(d.info)
    step_i = 0
    missing_i = 0
    start_time = time.time()

    gr = Guided_Replay()
    with open('promt_text/gui-1.xml', 'r') as f:
        example_ui = f.read()
    with open('promt_text/guided_prompt.txt', 'r', encoding='utf-8') as file:
        example_gr_prompt = file.read()
    gr_prompt = example_gr_prompt.format(example_ui, example_ui)
    gr_prompt = gr_prompt.strip()
    gr.infer(gr_prompt, Flag=True)

    while step_i < len(step_outputs):
        logger.debug(step_outputs[step_i].step_text)
        page_source = d.dump_hierarchy(compressed=True, pretty=True) #PS:1
        xml_file = open(os.path.join(save_path, f'step_{step_i}_hierarchy.xml'), 'w', encoding='utf-8')
        xml_file.write(page_source)
        xml_file.close()
        adb.screen_shot(f'step_{step_i}', save_path) #PS:2

        if missing_i == 10:
            break

        if step_outputs[step_i].action.lower() != "scroll":
            ui = UI(os.path.join(save_path, f'step_{step_i}_hierarchy.xml'))
            html_code = ui.encoding()
            with open('mid_result/html_code.txt', 'a', encoding='utf-8') as file:
                file.write(f"{step_outputs[step_i].step_text}:\n")
                file.write(f"{html_code}\n")
                file.write("\n")


            title_prompt = """Question:\n"""
            if step_outputs[step_i].action.lower() == "input":
                step = "[{}] [{}] [{}]".format(step_outputs[step_i].action, step_outputs[step_i].target,
                                               step_outputs[step_i].input)
            else:
                step = "[{}] [{}]".format(step_outputs[step_i].action, step_outputs[step_i].target)
            ui_prompt = """GUI screen: \n{}\n\n""".format(html_code)
            question_prompt = """If I need to {}, which component id should I operate on the GUI? ->\nAnswer:""".format(step)
            prompt = title_prompt + ui_prompt + question_prompt
            prompt = prompt.strip()

            recursive_flag, target_id = gr.infer(prompt,Flag=False) ##PS:7
            logger.info("""Operate on id={} in the GUI screen.""".format(target_id))

            if target_id is None:
                adb.back()
                logger.info("No component found!")
                os.rename(os.path.join(save_path, f'step_{step_i}_hierarchy.xml'),
                          os.path.join(save_path, f'step_{step_i}_missing_{missing_i}_hierarchy.xml'))
                os.rename(os.path.join(save_path, f'screenshot-step_{step_i}.png'),
                          os.path.join(save_path, f'screenshot-step_{step_i}_missing_{missing_i}.png'))
                missing_i += 1
                continue

            # Excute the action
            bounds = [ui.elements[target_id].bounding_box.x1, \
                      ui.elements[target_id].bounding_box.y1, \
                      ui.elements[target_id].bounding_box.x2, \
                      ui.elements[target_id].bounding_box.y2]
            if step_outputs[step_i].action.lower() == "tap":
                adb.click(bounds)
            elif step_outputs[step_i].action.lower() == "double-tap":
                adb.double_click(bounds)
            elif step_outputs[step_i].action.lower() == "long-tap":
                adb.long_click(bounds)
            elif step_outputs[step_i].action.lower() == "input":
                adb.input_text(bounds, step_outputs[step_i].input)

            if recursive_flag:
                logger.info("There is a MISSING step!")
                os.rename(os.path.join(save_path, f'step_{step_i}_hierarchy.xml'),
                          os.path.join(save_path, f'step_{step_i}_missing_{missing_i}_hierarchy.xml'))
                os.rename(os.path.join(save_path, f'screenshot-step_{step_i}.png'),
                          os.path.join(save_path, f'screenshot-step_{step_i}_missing_{missing_i}.png'))
                missing_i += 1

            else:
                adb.screen_shot(f'step_{step_i}', save_path)
                step_i += 1

        else:
            direction = 'up' if 'up' in step_outputs[step_i].target else 'down'
            adb.scroll(direction)
            step_i += 1

        time.sleep(1)

    time_spend = time.time() - start_time
    print("Prcessing time", time_spend)
    if missing_i == 10:
        print("ERROR!!!!")

