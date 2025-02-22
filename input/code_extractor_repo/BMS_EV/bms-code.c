/**
 * Battery Management System (BMS) for Electric Vehicle
 * 
 * Features:
 * - Cell voltage monitoring
 * - Temperature monitoring
 * - State of Charge (SoC) estimation
 * - Cell balancing
 * - Fault detection
 */

#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

// Configuration parameters
#define NUM_CELLS                12      // Number of cells in the battery pack
#define NUM_TEMP_SENSORS         8       // Number of temperature sensors
#define CELL_VOLTAGE_MIN         2800    // Minimum cell voltage in mV (2.8V)
#define CELL_VOLTAGE_MAX         4200    // Maximum cell voltage in mV (4.2V)
#define CELL_VOLTAGE_BALANCE     3900    // Voltage threshold for balancing in mV (3.9V)
#define CELL_VOLTAGE_IMBALANCE   50      // Maximum allowed voltage difference between cells in mV
#define TEMP_MIN                 0       // Minimum safe temperature in Celsius
#define TEMP_MAX                 45      // Maximum safe temperature in Celsius
#define CURRENT_MAX              100     // Maximum discharge current in Amperes
#define ADC_RESOLUTION           4096    // 12-bit ADC
#define ADC_REFERENCE_VOLTAGE    5000    // 5V reference in mV

// BMS states
typedef enum {
    BMS_STATE_INIT,
    BMS_STATE_IDLE,
    BMS_STATE_CHARGING,
    BMS_STATE_DISCHARGING,
    BMS_STATE_BALANCING,
    BMS_STATE_FAULT
} bms_state_t;

// Fault codes
typedef enum {
    FAULT_NONE                = 0x00,
    FAULT_CELL_UNDERVOLTAGE   = 0x01,
    FAULT_CELL_OVERVOLTAGE    = 0x02,
    FAULT_PACK_UNDERVOLTAGE   = 0x04,
    FAULT_PACK_OVERVOLTAGE    = 0x08,
    FAULT_OVER_TEMPERATURE    = 0x10,
    FAULT_UNDER_TEMPERATURE   = 0x20,
    FAULT_OVERCURRENT         = 0x40,
    FAULT_CELL_IMBALANCE      = 0x80
} fault_code_t;

// BMS data structure
typedef struct {
    bms_state_t state;
    uint16_t cell_voltages[NUM_CELLS];       // in mV
    int8_t temperatures[NUM_TEMP_SENSORS];   // in Celsius
    int32_t current;                         // in mA, positive for discharge
    uint8_t soc;                             // State of Charge in percentage (0-100%)
    uint32_t capacity_remaining;             // in mAh
    uint32_t capacity_full;                  // in mAh
    bool balancing_active[NUM_CELLS];
    uint8_t fault_code;
} bms_data_t;

// Function prototypes
void bms_init(bms_data_t *bms);
void bms_update_measurements(bms_data_t *bms);
void bms_update_soc(bms_data_t *bms);
void bms_perform_balancing(bms_data_t *bms);
void bms_check_faults(bms_data_t *bms);
void bms_state_machine(bms_data_t *bms);
void bms_control_outputs(bms_data_t *bms);

// Simulated hardware interfaces
uint16_t adc_read_cell_voltage(uint8_t cell_index);
int8_t adc_read_temperature(uint8_t sensor_index);
int32_t adc_read_current(void);
void set_balance_switch(uint8_t cell_index, bool state);
void set_charger_enable(bool state);
void set_discharge_enable(bool state);

// Main function
int main(void) {
    bms_data_t bms;
    bms_init(&bms);
    
    // Main BMS loop
    while (1) {
        // Update sensor readings
        bms_update_measurements(&bms);
        
        // Estimate State of Charge
        bms_update_soc(&bms);
        
        // Check for faults
        bms_check_faults(&bms);
        
        // Run state machine
        bms_state_machine(&bms);
        
        // Perform cell balancing if needed
        bms_perform_balancing(&bms);
        
        // Control outputs based on state
        bms_control_outputs(&bms);
        
        // Print status (in a real system, this would be communication with main ECU)
        printf("BMS State: %d, SoC: %d%%, Fault Code: 0x%02X\n", 
               bms.state, bms.soc, bms.fault_code);
        
        // Delay for next cycle (simulated)
        // In a real system, this would be a proper timer-based execution
        // sleep(100); // 100ms update rate
    }
    
    return 0;
}

// Initialize BMS
void bms_init(bms_data_t *bms) {
    memset(bms, 0, sizeof(bms_data_t));
    bms->state = BMS_STATE_INIT;
    bms->capacity_full = 50000; // 50Ah in mAh
    bms->capacity_remaining = 0;
    
    // Initial measurements
    bms_update_measurements(bms);
    bms_update_soc(bms);
    
    // Transition to idle state if no faults
    bms_check_faults(bms);
    if (bms->fault_code == FAULT_NONE) {
        bms->state = BMS_STATE_IDLE;
    } else {
        bms->state = BMS_STATE_FAULT;
    }
}

// Update all measurements from sensors
void bms_update_measurements(bms_data_t *bms) {
    // Read all cell voltages
    for (int i = 0; i < NUM_CELLS; i++) {
        bms->cell_voltages[i] = adc_read_cell_voltage(i);
    }
    
    // Read all temperature sensors
    for (int i = 0; i < NUM_TEMP_SENSORS; i++) {
        bms->temperatures[i] = adc_read_temperature(i);
    }
    
    // Read current sensor
    bms->current = adc_read_current();
}

// Update State of Charge estimation
void bms_update_soc(bms_data_t *bms) {
    // Simple SoC calculation based on average cell voltage
    // In a real system, this would use coulomb counting and more sophisticated algorithms
    
    uint32_t avg_voltage = 0;
    for (int i = 0; i < NUM_CELLS; i++) {
        avg_voltage += bms->cell_voltages[i];
    }
    avg_voltage /= NUM_CELLS;
    
    // Linear approximation between min and max voltage
    if (avg_voltage <= CELL_VOLTAGE_MIN) {
        bms->soc = 0;
    } else if (avg_voltage >= CELL_VOLTAGE_MAX) {
        bms->soc = 100;
    } else {
        bms->soc = (avg_voltage - CELL_VOLTAGE_MIN) * 100 / (CELL_VOLTAGE_MAX - CELL_VOLTAGE_MIN);
    }
    
    // Calculate remaining capacity
    bms->capacity_remaining = (bms->capacity_full * bms->soc) / 100;
}

// Perform cell balancing if needed
void bms_perform_balancing(bms_data_t *bms) {
    // Only balance during charging or dedicated balancing state
    if (bms->state != BMS_STATE_CHARGING && bms->state != BMS_STATE_BALANCING) {
        // Turn off all balancing
        for (int i = 0; i < NUM_CELLS; i++) {
            if (bms->balancing_active[i]) {
                bms->balancing_active[i] = false;
                set_balance_switch(i, false);
            }
        }
        return;
    }
    
    // Find maximum cell voltage
    uint16_t max_voltage = 0;
    for (int i = 0; i < NUM_CELLS; i++) {
        if (bms->cell_voltages[i] > max_voltage) {
            max_voltage = bms->cell_voltages[i];
        }
    }
    
    // Only balance if max voltage is above threshold
    if (max_voltage < CELL_VOLTAGE_BALANCE) {
        // Turn off all balancing
        for (int i = 0; i < NUM_CELLS; i++) {
            if (bms->balancing_active[i]) {
                bms->balancing_active[i] = false;
                set_balance_switch(i, false);
            }
        }
        return;
    }
    
    // Enable balancing for cells above threshold
    for (int i = 0; i < NUM_CELLS; i++) {
        bool should_balance = (bms->cell_voltages[i] > CELL_VOLTAGE_BALANCE) && 
                              (bms->cell_voltages[i] > (max_voltage - CELL_VOLTAGE_IMBALANCE));
        
        if (should_balance != bms->balancing_active[i]) {
            bms->balancing_active[i] = should_balance;
            set_balance_switch(i, should_balance);
        }
    }
}

// Check for fault conditions
void bms_check_faults(bms_data_t *bms) {
    uint8_t new_faults = FAULT_NONE;
    
    // Check cell voltages
    uint16_t min_voltage = UINT16_MAX;
    uint16_t max_voltage = 0;
    
    for (int i = 0; i < NUM_CELLS; i++) {
        if (bms->cell_voltages[i] < min_voltage) {
            min_voltage = bms->cell_voltages[i];
        }
        if (bms->cell_voltages[i] > max_voltage) {
            max_voltage = bms->cell_voltages[i];
        }
        
        // Check individual cell voltages
        if (bms->cell_voltages[i] < CELL_VOLTAGE_MIN) {
            new_faults |= FAULT_CELL_UNDERVOLTAGE;
        }
        if (bms->cell_voltages[i] > CELL_VOLTAGE_MAX) {
            new_faults |= FAULT_CELL_OVERVOLTAGE;
        }
    }
    
    // Check for cell imbalance
    if ((max_voltage - min_voltage) > CELL_VOLTAGE_IMBALANCE) {
        new_faults |= FAULT_CELL_IMBALANCE;
    }
    
    // Check pack voltage
    uint32_t pack_voltage = 0;
    for (int i = 0; i < NUM_CELLS; i++) {
        pack_voltage += bms->cell_voltages[i];
    }
    
    if (pack_voltage < (CELL_VOLTAGE_MIN * NUM_CELLS)) {
        new_faults |= FAULT_PACK_UNDERVOLTAGE;
    }
    if (pack_voltage > (CELL_VOLTAGE_MAX * NUM_CELLS)) {
        new_faults |= FAULT_PACK_OVERVOLTAGE;
    }
    
    // Check temperatures
    for (int i = 0; i < NUM_TEMP_SENSORS; i++) {
        if (bms->temperatures[i] < TEMP_MIN) {
            new_faults |= FAULT_UNDER_TEMPERATURE;
        }
        if (bms->temperatures[i] > TEMP_MAX) {
            new_faults |= FAULT_OVER_TEMPERATURE;
        }
    }
    
    // Check current
    if (bms->current > (CURRENT_MAX * 1000)) { // Convert A to mA
        new_faults |= FAULT_OVERCURRENT;
    }
    
    // Update fault code
    bms->fault_code = new_faults;
}

// State machine implementation
void bms_state_machine(bms_data_t *bms) {
    // Handle fault state with priority
    if (bms->fault_code != FAULT_NONE) {
        bms->state = BMS_STATE_FAULT;
        return;
    }
    
    // State transitions based on current state and conditions
    switch (bms->state) {
        case BMS_STATE_INIT:
            // Transition from init to idle once initialization is complete
            bms->state = BMS_STATE_IDLE;
            break;
            
        case BMS_STATE_IDLE:
            // Transition to charging if current is negative (charging)
            if (bms->current < -500) { // -500mA threshold
                bms->state = BMS_STATE_CHARGING;
            }
            // Transition to discharging if current is positive (discharging)
            else if (bms->current > 500) { // 500mA threshold
                bms->state = BMS_STATE_DISCHARGING;
            }
            // Transition to balancing if cells need balancing
            else {
                uint16_t min_voltage = UINT16_MAX;
                uint16_t max_voltage = 0;
                
                for (int i = 0; i < NUM_CELLS; i++) {
                    if (bms->cell_voltages[i] < min_voltage) {
                        min_voltage = bms->cell_voltages[i];
                    }
                    if (bms->cell_voltages[i] > max_voltage) {
                        max_voltage = bms->cell_voltages[i];
                    }
                }
                
                if ((max_voltage > CELL_VOLTAGE_BALANCE) && 
                    ((max_voltage - min_voltage) > CELL_VOLTAGE_IMBALANCE)) {
                    bms->state = BMS_STATE_BALANCING;
                }
            }
            break;
            
        case BMS_STATE_CHARGING:
            // Return to idle if no longer charging
            if (bms->current > -500) { // -500mA threshold
                bms->state = BMS_STATE_IDLE;
            }
            break;
            
        case BMS_STATE_DISCHARGING:
            // Return to idle if no longer discharging
            if (bms->current < 500) { // 500mA threshold
                bms->state = BMS_STATE_IDLE;
            }
            break;
            
        case BMS_STATE_BALANCING:
            // Check if balancing is complete
            uint16_t min_voltage = UINT16_MAX;
            uint16_t max_voltage = 0;
            
            for (int i = 0; i < NUM_CELLS; i++) {
                if (bms->cell_voltages[i] < min_voltage) {
                    min_voltage = bms->cell_voltages[i];
                }
                if (bms->cell_voltages[i] > max_voltage) {
                    max_voltage = bms->cell_voltages[i];
                }
            }
            
            // Return to idle if balancing is no longer needed
            if ((max_voltage <= CELL_VOLTAGE_BALANCE) || 
                ((max_voltage - min_voltage) <= CELL_VOLTAGE_IMBALANCE)) {
                bms->state = BMS_STATE_IDLE;
            }
            // Transition to charging if current indicates charging
            else if (bms->current < -500) {
                bms->state = BMS_STATE_CHARGING;
            }
            break;
            
        case BMS_STATE_FAULT:
            // Stay in fault state until faults are cleared
            if (bms->fault_code == FAULT_NONE) {
                bms->state = BMS_STATE_IDLE;
            }
            break;
            
        default:
            // Invalid state, reset to init
            bms->state = BMS_STATE_INIT;
            break;
    }
}

// Control outputs based on current state
void bms_control_outputs(bms_data_t *bms) {
    switch (bms->state) {
        case BMS_STATE_INIT:
        case BMS_STATE_FAULT:
            // Disable both charging and discharging in init or fault states
            set_charger_enable(false);
            set_discharge_enable(false);
            break;
            
        case BMS_STATE_IDLE:
        case BMS_STATE_BALANCING:
            // Allow both charging and discharging in idle or balancing states
            set_charger_enable(true);
            set_discharge_enable(true);
            break;
            
        case BMS_STATE_CHARGING:
            // Allow charging but prevent discharging
            set_charger_enable(true);
            set_discharge_enable(false);
            break;
            
        case BMS_STATE_DISCHARGING:
            // Allow discharging but prevent charging
            set_charger_enable(false);
            set_discharge_enable(true);
            break;
            
        default:
            // Safety default - disable both
            set_charger_enable(false);
            set_discharge_enable(false);
            break;
    }
}

//------------------------------------------------------------------------------
// Simulated hardware interface implementations
// In a real system, these would interface with actual ADCs and GPIO pins
//------------------------------------------------------------------------------

uint16_t adc_read_cell_voltage(uint8_t cell_index) {
    // Simulate cell voltages around 3.7V (3700mV) with some variation
    uint16_t base_voltage = 3700;
    uint16_t variation = rand() % 50;
    
    // Add some discharge curve simulation based on cell index
    if (cell_index % 3 == 0) {
        return base_voltage - 20 + variation;
    } else if (cell_index % 3 == 1) {
        return base_voltage + variation;
    } else {
        return base_voltage + 30 + variation;
    }
}

int8_t adc_read_temperature(uint8_t sensor_index) {
    // Simulate temperatures around 25°C with some variation
    int8_t base_temp = 25;
    int8_t variation = rand() % 5;
    
    // Distribute temperatures based on sensor location
    if (sensor_index < NUM_TEMP_SENSORS / 2) {
        return base_temp + variation;
    } else {
        return base_temp + 2 + variation;
    }
}

int32_t adc_read_current(void) {
    // Simulate current: positive for discharge, negative for charge
    // Range: -20A to +50A (-20000mA to +50000mA)
    static int is_charging = 0;
    
    // Randomly switch between charging and discharging
    if (rand() % 100 == 0) {
        is_charging = !is_charging;
    }
    
    if (is_charging) {
        return -(5000 + (rand() % 15000)); // -5A to -20A
    } else {
        return 2000 + (rand() % 30000);    // 2A to 32A
    }
}

void set_balance_switch(uint8_t cell_index, bool state) {
    // In a real system, this would control balancing MOSFETs
    printf("Cell %d balancing: %s\n", cell_index, state ? "ON" : "OFF");
}

void set_charger_enable(bool state) {
    // In a real system, this would control the charger enable signal
    printf("Charger: %s\n", state ? "ENABLED" : "DISABLED");
}

void set_discharge_enable(bool state) {
    // In a real system, this would control the discharge enable signal
    printf("Discharge: %s\n", state ? "ENABLED" : "DISABLED");
}
