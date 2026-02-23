from aiogram.fsm.state import State, StatesGroup

class DefectReportStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_severity = State()
    waiting_for_impact_area = State()
