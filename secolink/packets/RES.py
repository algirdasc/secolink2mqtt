from .packet import Packet

class RES(Packet):
        
    def mqtt_other_payload(self) -> str:
        if self.data == 'OK':
            return 'Command successful'
        elif self.data == 'ERR_PIN_REQUIRED':
            return 'PIN required'
        elif self.data == 'ERR_WRONG_PIN':
            return 'Wrong PIN received'
        elif self.data == 'ERR_COMMAND_FAILED':
            return 'Command failed'
        elif self.data == 'ERR_NO_SPACE_FOR_NUMBER':
            return 'No space to add reporting number'
        elif self.data == 'ERR_SERIAL_NOT_CONNECTED':
            return 'Module not connected to CP'
        elif self.data == 'ERR_SERIAL_BAD_PC_PASSWORD':
            return 'Wrong PC password'
        else:
            return self.data

    def mqtt_suffix(self) -> str:
        return 'result'