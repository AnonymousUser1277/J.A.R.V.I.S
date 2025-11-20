"""
Device monitoring
USB, HDMI, Bluetooth devices
"""

import time
import wmi
 
def categorize_device_type(device):
    """Categorize device based on its properties"""
    device_id = device.DeviceID.upper()
    name = device.Name.upper() if device.Name else ""
    pnp_class = device.PNPClass.upper() if device.PNPClass else ""
    
    if 'USB' in device_id:
        if 'STORAGE' in name or 'DISK' in name or 'MASS' in name:
            return 'USB Storage'
        elif 'MOUSE' in name:
            return 'USB Mouse'
        elif 'KEYBOARD' in name or 'KBD' in name:
            return 'USB Keyboard'
        elif 'CAMERA' in name or 'WEBCAM' in name:
            return 'USB Camera'
        else:
            return 'USB Device'
    
    if 'DISPLAY' in pnp_class or 'MONITOR' in pnp_class or 'MONITOR' in name:
        if 'HDMI' in name:
            return 'HDMI Monitor'
        elif 'DISPLAYPORT' in name:
            return 'DisplayPort Monitor'
        else:
            return 'Monitor'
    
    if 'KEYBOARD' in pnp_class or 'KEYBOARD' in name:
        return 'Keyboard'
    if 'MOUSE' in pnp_class or 'MOUSE' in name:
        return 'Mouse'
    if 'DISKDRIVE' in pnp_class or 'DISK' in name:
        return 'Disk Drive'
    
    return device.PNPClass or 'Physical Device'

def get_connected_devices():
    """Get all connected physical port devices (USB, HDMI, etc.)"""
    devices = {}
    try:
        c = wmi.WMI()
        for device in c.Win32_PnPEntity():
            try:
                if device.Status == 'OK' and device.Name and device.DeviceID:
                    device_class = (device.PNPClass or '').upper()
                    device_name = device.Name.upper()
                    device_id = device.DeviceID.upper()
                    
                    # Skip bluetooth, audio, network adapters
                    skip_keywords = [
                        'BLUETOOTH', 'AUDIO', 'SOUND', 'SPEAKER', 'MICROPHONE',
                        'AVRCP', 'HANDS-FREE', 'A2DP', 'NETWORK', 'ETHERNET',
                        'WIFI', 'WAN', 'VMWARE', 'MEDIA', 'STREAMING'
                    ]
                    
                    should_skip = any(
                        keyword in device_name or keyword in device_id
                        for keyword in skip_keywords
                    )
                    
                    if should_skip:
                        continue
                    
                    # Only include physical port devices
                    is_physical_port_device = (
                        'USB' in device_id or
                        device_class in ['MOUSE', 'KEYBOARD', 'MONITOR', 'DISKDRIVE', 'USB', 'WPD', 'PORTS'] or
                        'MOUSE' in device_name or
                        'KEYBOARD' in device_name or
                        'MONITOR' in device_name or
                        'HDMI' in device_name or
                        'DISPLAYPORT' in device_name or
                        'DISPLAY' in device_name or
                        'DISK' in device_name or
                        'STORAGE' in device_name
                    )
                    
                    if is_physical_port_device:
                        device_type = categorize_device_type(device)
                        
                        devices[device.DeviceID] = {
                            'name': device.Name,
                            'description': device.Description or device.Name,
                            'manufacturer': device.Manufacturer,
                            'status': device.Status,
                            'type': device_type,
                            'class': device.PNPClass
                        }
            except Exception as e:
                print(f"Device enumeration error: {e}")
                continue  
    except Exception as e:
        print(f"Error getting connected devices: {e}")
    
    return devices

def port_monitor(context_manager, poll=...):
    """Monitor USB/HDMI/DisplayPort devices"""
    last_devices = {}
    
    while True:
        try:
            current = get_connected_devices()
            
            # New devices
            for dev_id, info in current.items():
                if dev_id not in last_devices:
                    context_manager.update_device(dev_id, info)
            
            # Removed devices
            for dev_id in last_devices:
                if dev_id not in current:
                    context_manager.remove_device(dev_id)
            
            last_devices = current
        except Exception as e:
            print(f"Port monitor error: {e}")
        
        time.sleep(poll)

def get_bluetooth_devices():
    """Get all connected Bluetooth devices"""
    bt_devices = {}
    try:
        c = wmi.WMI()
        for device in c.Win32_PnPEntity():
            if device.Status == 'OK' and device.Name and device.DeviceID:
                device_name = device.Name.upper()
                device_id = device.DeviceID.upper()
                
                # Only include Bluetooth devices
                is_bluetooth = (
                    'BTHENUM' in device_id or
                    'BLUETOOTH' in device_name or
                    'BLUETOOTH' in device_id
                )
                
                if is_bluetooth:
                    # Categorize Bluetooth device type
                    bt_type = 'Bluetooth Device'
                    if 'MOUSE' in device_name:
                        bt_type = 'Bluetooth Mouse'
                    elif 'KEYBOARD' in device_name:
                        bt_type = 'Bluetooth Keyboard'
                    elif 'HEADPHONE' in device_name or 'HEADSET' in device_name:
                        bt_type = 'Bluetooth Headset'
                    elif 'SPEAKER' in device_name:
                        bt_type = 'Bluetooth Speaker'
                    elif 'AUDIO' in device_name:
                        bt_type = 'Bluetooth Audio'
                    
                    bt_devices[device.DeviceID] = {
                        'name': device.Name,
                        'description': device.Description or device.Name,
                        'status': device.Status,
                        'type': bt_type
                    }
    except Exception as e:
        print(f"Error getting Bluetooth devices: {e}")
    
    return bt_devices

def bluetooth_monitor(context_manager, poll=...):
    """Monitor Bluetooth device connections"""
    last_bt_devices = {}
    
    while True:
        try:
            current = get_bluetooth_devices()
            
            # New Bluetooth devices
            for dev_id, info in current.items():
                if dev_id not in last_bt_devices:
                    context_manager.update_bluetooth_device(dev_id, info)
            
            # Removed Bluetooth devices
            for dev_id in last_bt_devices:
                if dev_id not in current:
                    context_manager.remove_bluetooth_device(dev_id)
            
            last_bt_devices = current
        except Exception as e:
            print(f"Bluetooth monitor error: {e}")
        
        time.sleep(poll)