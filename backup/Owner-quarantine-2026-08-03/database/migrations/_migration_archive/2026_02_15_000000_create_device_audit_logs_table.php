<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    /**
     * Run the migrations.
     * M3: Device Management - Device Audit Logs
     */
    public function up(): void
    {
        Schema::create('device_audit_logs', function (Blueprint $table) {
            $table->id();

            // Foreign keys
            $table->unsignedBigInteger('device_id')->index()->comment('FK -> devices.id');
            $table->unsignedBigInteger('user_id')->index()->comment('FK -> users.id');

            // Audit information
            $table->string('action', 50)->comment('Action type: created, updated, status_changed, venue_assigned');
            $table->json('old_values')->nullable()->comment('Previous state');
            $table->json('new_values')->nullable()->comment('New state');
            $table->text('description')->nullable()->comment('Human-readable change description');

            $table->timestamp('created_at')->useCurrent();

            // Indexes
            $table->index(['device_id', 'created_at']);
            $table->index(['user_id', 'created_at']);
            $table->index('created_at');

            // Foreign key constraints
            $table->foreign('device_id')->references('id')->on('devices')->onDelete('cascade');
            $table->foreign('user_id')->references('id')->on('users')->onDelete('cascade');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('device_audit_logs');
    }
};
