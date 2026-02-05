# Additional Hints for Traccar Adapter
The `traccar` adapter uses Traccar's WebSocket connection to work with realtime updates. The adapter reacts as follows:

- When a device online event is received, the vehicle is added to the internal cache
- When a position update is received, the update is sent as `PhysicalPositionUpdate`. If a vehicle has not been technically logged on yet, the `TechnicalLogOn` is sent.
- When a device inactive event is received, the message for `TechnicalLogOff` is sent.

To use Traccar for integration with `avl2gtfsrt`, Traccar should be configured with some features:

- For each device representing a vehicle, add a custom custom property `vehicleId` which represents the published vehicle ID. If not set, the device's name is used as fallback.
- For each device, set the property `deviceInactivityStart` to a proper value (in milliseconds!) for when a device is considered as 'inactive'; this is required for sending the device inactive events. If not set, a vehicle may remain technically logged on even if it is not active anymore.
- Add notifications over `web` channel for when a device becomes online or inactive. This is required to detect newly added devices for the transformation to technical vehicle log on and technical vehicle log off. If not configured, there's no option for getting information about changed device states.