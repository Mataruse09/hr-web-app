-- Add missing working_hours column to attendance table
ALTER TABLE attendance ADD COLUMN working_hours DECIMAL(5,2) DEFAULT NULL AFTER status;