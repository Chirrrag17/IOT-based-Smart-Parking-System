```cpp
#include <Servo.h>

// Create servo object
Servo gateServo;

// Pin definitions
const int IRSensor = 7;   // IR sensor OUT pin
const int LED = 8;        // LED pin
const int servoPin = 6;   // Servo signal pin
const int trigPin = 2;    // Ultrasonic TRIG pin
const int echoPin = 3;    // Ultrasonic ECHO pin

// Distance threshold in centimeters
const int thresholdDistance = 5;

// Servo positions
const int GATE_CLOSED = 0;
const int GATE_OPEN = 90;

// Function to measure distance
long getDistance()
{
    digitalWrite(trigPin, LOW);
    delayMicroseconds(2);

    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);

    // Timeout prevents waiting indefinitely
    long duration = pulseIn(echoPin, HIGH, 30000);

    // Return -1 if no echo is received
    if (duration == 0)
    {
        return -1;
    }

    // Convert echo duration to centimeters
    long distance = duration * 0.034 / 2;

    return distance;
}

void setup()
{
    Serial.begin(115200);
    Serial.println("Smart Parking System Starting...");

    pinMode(IRSensor, INPUT);
    pinMode(LED, OUTPUT);

    pinMode(trigPin, OUTPUT);
    pinMode(echoPin, INPUT);

    gateServo.attach(servoPin);

    // Initial state: gate closed
    gateServo.write(GATE_CLOSED);
    digitalWrite(LED, HIGH);

    Serial.println("System Ready");
}

void loop()
{
    // Read IR sensor
    int IR_Status = digitalRead(IRSensor);

    // Measure ultrasonic distance
    long distance = getDistance();

    // Display sensor readings
    Serial.print("IR: ");
    Serial.print(IR_Status);

    Serial.print(" | Distance: ");

    if (distance == -1)
    {
        Serial.println("No echo");
    }
    else
    {
        Serial.print(distance);
        Serial.println(" cm");
    }

    // Detect an object if:
    // 1. IR sensor output is LOW
    // 2. Valid ultrasonic distance is below threshold
    bool objectDetected =
        (IR_Status == LOW) ||
        (distance > 0 && distance < thresholdDistance);

    if (objectDetected)
    {
        // Object detected: open gate
        digitalWrite(LED, LOW);
        gateServo.write(GATE_OPEN);

        Serial.println("Object Detected - Gate Open");
    }
    else
    {
        // No object detected: close gate
        digitalWrite(LED, HIGH);
        gateServo.write(GATE_CLOSED);

        Serial.println("No Object - Gate Closed");
    }

    delay(150);
}
```
