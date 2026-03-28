#include <LiquidCrystal.h>

// LCD pin configuration
const int rs = D1, en = D2, d4 = D3, d5 = D4, d6 = D5, d7 = D6;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

String message = "";
unsigned long lastScrollTime = 0;
int scrollIndex = 0;
bool scrolling = false;

void setup() {
  Serial.begin(9600);
  lcd.begin(16, 2);
  lcd.clear();
  lcd.print("ChatBot Ready");
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      scrollIndex = 0;
      scrolling = true;
    } else {
      message += c;
    }
  }

  if (scrolling) {
    if (millis() - lastScrollTime >= 500) {  // Scroll every 0.5 sec
      lcd.clear();
      String line1 = message.substring(scrollIndex, scrollIndex + 16);
      String line2 = message.length() > scrollIndex + 16 ? message.substring(scrollIndex + 16, scrollIndex + 32) : "";

      lcd.setCursor(0, 0);
      lcd.print(line1);
      lcd.setCursor(0, 1);
      lcd.print(line2);

      scrollIndex++;
      if (scrollIndex > message.length()) {
        scrollIndex = 0;
        scrolling = false;
        message = "";
        lcd.clear();
        lcd.print("ChatBot Ready");
      }

      lastScrollTime = millis();
    }
  }
}
