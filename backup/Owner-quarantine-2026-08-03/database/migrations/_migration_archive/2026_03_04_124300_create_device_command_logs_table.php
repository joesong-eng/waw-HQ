<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('device_command_logs', function (Blueprint $table) {
            $table->id();
            $table->foreignId('device_id')->constrained('devices')->onDelete('cascade');
            $table->foreignId('user_id')->constrained('users')->onDelete('cascade');
            $table->enum('command_type', ['assign_credit', 'settle_credit']);
            $table->string('transaction_id', 100)->nullable();
            $table->json('request_payload')->nullable();
            $table->json('response_payload')->nullable();
            $table->enum('status', ['sent', 'success', 'failed', 'timeout'])->default('sent');
            $table->decimal('estimated_amount', 12, 2)->nullable();
            $table->decimal('actual_amount', 12, 2)->nullable();
            $table->text('error_message')->nullable();
            $table->timestamps();

            $table->index('device_id');
            $table->index('transaction_id');
            $table->index('status');
            $table->index('created_at');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('device_command_logs');
    }
};
