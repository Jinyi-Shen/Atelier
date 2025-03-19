import logging
import os
from rich.logging import RichHandler


def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    console_log = RichHandler(
        level="NOTSET",
        log_time_format="%Y-%m-%d %H:%M:%S",
        omit_repeated_times=False,
    )
    console_log.setLevel(logging.INFO)

    log_file = os.path.join(os.path.dirname(__file__), "..", "..", "log", "debug.log")
    if not os.path.exists(os.path.dirname(log_file)):
        os.makedirs(os.path.dirname(log_file))
    file_log = logging.FileHandler(filename=log_file)
    file_log.setLevel(logging.INFO)

    log_format = "%(asctime)s [%(filename)s:%(lineno)s %(funcName)s()] %(levelname)s: %(message)s"
    formatter_console = logging.Formatter(log_format)
    formatter_file = logging.Formatter(log_format)

    # console_log.setFormatter(formatter_console)
    file_log.setFormatter(formatter_file)

    logger.addHandler(console_log)
    logger.addHandler(file_log)

    return logger


logger = setup_logger()


def logger_add_query_prompt(AgentName: str, sys_prompt: str=None, human_prompts: list=[]):
    msg = "\n>>> {AgentName} >>>".format(AgentName=AgentName)
    if sys_prompt is not None:
        msg += "\n>>>>>>>>>> System Prompt >>>>>>>>>>\n{sys_prompt}\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>".format(sys_prompt=sys_prompt)
    for human_prompt in human_prompts:
        msg += "\n>>>>>>>>>> Human Prompt >>>>>>>>>>\n{human_prompt}\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>".format(human_prompt=human_prompt)
    logger.info(msg)

def logger_add_response(AgentName: str, response: str):
    msg = "\n>>> {AgentName} >>>".format(AgentName=AgentName)
    msg += "\n>>>>>>>>>> Assistant Prompt >>>>>>>>>>\n{response}\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>".format(response=response)
    logger.info(msg)

def logger_add_midstep(AgentName: str, mid_steps: list[str]):
    msg = "\n>>> {AgentName} >>>".format(AgentName=AgentName)
    for mid_step in mid_steps:
        msg += "\n>>>>>>>>>> Assistant Prompt Mid >>>>>>>>>>\n{mid_step}\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>".format(mid_step=mid_step)
    logger.info(msg)


if __name__ == '__main__':
    logger_add_query_prompt("Agent1", "This is a system prompt.", ["This is a human prompt.", "This is another human prompt."])
    logger_add_query_prompt("Agent1", None, ["This is a human prompt.", "This is another human prompt."])
    logger_add_query_prompt("Agent1", "This is a system prompt.", [])
    logger_add_query_prompt("Agent1", None, [])
    logger_add_response("Agent1", "This is a response.")
    logger_add_midstep("Agent1", ["This is a midstep.", "This is another midstep."])
