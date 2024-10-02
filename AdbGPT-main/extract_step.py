import re
from loguru import logger

from ChatGPT import ChatGPT
import cfgs


class STEP():
    def __init__(self, step_text):
        self.step_text = step_text
        self.action, self.target, self.input = self.step_parse()

    def step_parse(self):
        m = re.findall(r'\[(.*?)\]', self.step_text)
        if not self.is_step(m):
            print(f'Error: No actions found: {self.step_text}')
            return None

        action = None
        target = None
        input = None

        # Considering cases:
        # - [Tap] "home"
        # - [Tap] ["home"]
        # - [Input] ["home", "1"]
        # - [Input] ["home"]
        # NOT considering case:
        # - [Tap] ["home"] or [Tap] [button]
        # - 1. [Input] ["key", "shop"] \n [Input] ["value", "*"]
        if len(m) == 1:
            action = m[0]
            target = self.step_text.split(f"[{m[0]}]")[-1].strip()
        elif len(m) >= 2:
            if 'input' not in m[0].lower():
                action = m[0]
                target = m[1]
            else:
                action = m[0]
                target = m[1].strip()
                
                if len(m) > 2: 
                    input = m[2].strip()
                else:
                    input = cfgs.RANDOM_INPUT_TEXT

        return action, target, input

    def is_step(self, list_of_variable):
        for v in list_of_variable:
            if v.lower() in cfgs.ACTION_LISTS:
                return True
        return False




class Extract_Steps():
    def __init__(self):
        self.chatgpt = ChatGPT()
        self.chatgpt.initialize_chatgpt()

    def infer(self, question):
        response = self.chatgpt.infer(question)
#         response = """The action sequence can be converted as follows:
# 1. [Input] ["key", "shop"]
#    [Input] ["value", "*"]
#    [Input] ["max. age", "0"]
# 2. [Tap] ["DONE"]
#    [Tap] ["back"] (assuming this goes back to the main screen)"""

        output = []
        step = 1
        for line in response.split('\n'):
            line = line.strip()
            if re.match(f"{step}\. \[([A-Za-z0-9.^_-]+)\]", line) is not None:
                s = STEP(line.split(f"{step}. ",1)[-1])
                logger.info('\n{} \n  >>>> STEP-{}: [{}] [{}] [{}]'.format(
                                        line, step, s.action, s.target, s.input))
                output.append(s)
                step += 1
        return output




if __name__ == '__main__':
    bug_description = """1. Go to Messaging\n2. Create a new conversation\n3. create a name with '123' \n4. Tap this conversation \n5. input 'LY' \n 6. Send Message\n 7. Return to previous screen """
    # bug_description = """1. Go to Messaging\n2. Long tap the '123'\n3. click delete and tap Sure"""
    # bug_description = """1. Open F-Droid\n2. Click "Settings" tab\n3. Scroll down to "Display" section\n4. click on "Theme"\n5. With the theme selector open (you can see choices like "Light", "Dark", "Night") tilt the device to change the orientation. If device did not crash yet, tilt it back to change orientation back."""
    # bug_description = """1. Open ATimeTracker,then make sound is enabled in Settings of ATimeTracker.\n2. Go to Android main view/screen (i.e. making sure ATimeTracker is not in the foreground).\n3. Start ATimeTracker.\n4. Start or stop an existing activity"""
    # bug_description = """1. Open AnkiDroid\n2. Press on + and choose Add card\n3. Press on attach and choose Add image\n4. Select Camera\n5. go to home"""
    # bug_description = """1. Open Messaging\n 2. click more ,then Go to Setting\n3. click Advance \n4. tap phone number"""
    # bug_description = """1. Open Messaging\n 2. click more ,then Go to Setting\n3.  Tap phone number after clicking Advance"""
    # bug_description = """1.Press 'paperclip' button to 'Add media'.\n 2.Select first image \n 3.Repeat to add second image"""

    action_prompt = """Available actions: [tap, input, scroll, double tap, long tap]\n"""
    primtive_prompt = """Action primitives: [Tap] [Component], [Scroll] [Direction], [Input] [Component] [Value], [Double-tap] [Component], [Long-tap] [Component]\n"""
    example_prompt = """Question: Extract the entity from the following ->
    "1. Open bookmark 
    2. Tap "add new bookmark" and create a name with "a" 
    3. Create another one with name "b" 
    4. Click "a" 
    5. Go back to bookmark after changing name "a" to "b" 
    6. App crash"\n"""
    cot_prompt = """Answer: 
    1st step is "Open bookmark". The action is "open" and the target component is "bookmark". However, there is no explicit "open" in the Available actions list. Therefore, we select the closest semantic action "tap". Following the Action primitives, the entity of the step is [Tap] ["bookmark"].
    2nd step is "Tap 'add new bookmark' and create a name with 'a'". Due to the conjunction word "and", this step can be separated into two sub-steps, "Tap 'add new bookmark'" and "create a name with 'a'". For the first sub-step, following the Action primitives, the entity is [Tap] ["add new bookmark"]. For the second sub-step, there is no explicit "create" in the Available actions list. Therefore, we select the closest semantic action "input". Following the Action primitives, the entity of the sub-step is [Input] ["name"] ["a"].
    3rd step is "Create another one with name 'b'". Due to its semantic meaning, this step is meant to repeat the previous steps to add another bookmark with name "b". Therefore, it should actually be the 2nd step, that is [Tap] ["add new bookmark"] and [Input] ["name"] ["b"].
    4th step is "Click 'a'". The action is "click" and the target component is "a". However, there is no explicit "click" in the Available actions list. Therefore, we select the closest semantic action "tap". Following the Action primitives, the entity of the step is [Tap] ["a"].
    5th step is "Go back to bookmark after changing name 'a' to 'b'". Due to the conjunction word "after", this step can be separated into two sub-steps, "Go back to bookmark" and "change name 'a' to 'b'". The conjunction word "after" also alters the temporal order of the sub-steps, that "change name 'a' to 'b'" should be executed first, followed by "go back to bookmark". For the first sub-step, there is no explicit "change" in the Available actions list. Therefore, we select the closest semantic action "input". Following the Action primitives, the entity of the sub-step is [Input] ["name"] ["b"]. For the second sub-step, there is no explicit "go back" in the Available actions list. Therefore, we select the closest semantic action "tap". Following the Action primitives, the entity of the sub-step is [Tap] ["back"].
    6th step is "App crash". This step does not have any operations.
    Overall, the extracted S2R entities are: 
    1. [Tap] ["bookmark"]
    2. [Tap] ["add new bookmark"]
    3. [Input] ["name"] ["a"]
    4. [Tap] ["add new bookmark"]
    5. [Input] ["name"] ["b"]
    6. [Tap] ["a"]
    7. [Input] ["name"] ["b"]
    8. [Tap] ["back"]\n
    """

    question_prompt = """Question: Convert the action sequence to "{}"\n Answer: """.format(bug_description)

    prompt = action_prompt + primtive_prompt + example_prompt + cot_prompt + question_prompt
    # prompt = action_prompt + primtive_prompt + question_prompt
    prompt = prompt.strip()

    es = Extract_Steps()
    output = es.infer(prompt)
    print(output)