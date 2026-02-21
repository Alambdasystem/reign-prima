"""Simple test to verify DearPyGUI works"""
import dearpygui.dearpygui as dpg

print("Creating DearPyGUI test window...")

dpg.create_context()

with dpg.window(label="TEST - Can you see this?", width=400, height=200, tag="test_win"):
    dpg.add_text("If you see this window, DearPyGUI is working!", color=[0, 255, 0])
    dpg.add_text("Close this window to continue", color=[255, 255, 0])
    dpg.add_button(label="Click Me!", callback=lambda: print("Button clicked!"))

dpg.create_viewport(title="DearPyGUI Test", width=400, height=200)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("test_win", True)

print("Window should be visible now!")
print("If you don't see it, check your taskbar or Alt+Tab")

while dpg.is_dearpygui_running():
    dpg.render_dearpygui_frame()

dpg.destroy_context()
print("Test complete!")
