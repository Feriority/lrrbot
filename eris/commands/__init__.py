import eris.commands.live
import eris.commands.time
import eris.commands.voice

def register(command_parser):
	eris.commands.live.register(command_parser)
	eris.commands.time.register(command_parser)
	eris.commands.voice.register(command_parser)
