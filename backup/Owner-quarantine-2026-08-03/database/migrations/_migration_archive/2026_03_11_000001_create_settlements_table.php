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
        Schema::create('settlements', function (Blueprint $table) {
            $table->id();
            $table->string('settlement_number', 100)->unique()->comment('結算單號');
            $table->foreignId('venue_id')->constrained('venues')->onDelete('restrict');
            $table->foreignId('device_owner_id')->constrained('users')->onDelete('restrict');
            $table->foreignId('venue_owner_id')->constrained('users')->onDelete('restrict');
            $table->date('period_start')->comment('結算期間開始');
            $table->date('period_end')->comment('結算期間結束');
            $table->decimal('total_revenue', 15, 2)->default(0.00)->comment('總營收');
            $table->decimal('device_owner_amount', 15, 2)->default(0.00)->comment('設備主分潤');
            $table->decimal('venue_owner_amount', 15, 2)->default(0.00)->comment('場地主分潤');
            $table->decimal('device_owner_share', 5, 2)->comment('設備主分潤比例');
            $table->decimal('venue_owner_share', 5, 2)->comment('場地主分潤比例');
            $table->enum('status', ['created', 'confirmed', 'paid', 'closed', 'disputed'])->default('created');
            $table->timestamp('confirmed_at')->nullable();
            $table->timestamp('paid_at')->nullable();
            $table->timestamp('closed_at')->nullable();
            $table->timestamp('disputed_at')->nullable();
            $table->text('dispute_reason')->nullable();
            $table->text('dispute_resolution')->nullable();
            $table->string('payment_proof_url', 500)->nullable();
            $table->timestamps();

            // Indexes
            $table->index('settlement_number');
            $table->index(['venue_id', 'period_start', 'period_end'], 'idx_venue_period');
            $table->index(['device_owner_id', 'status'], 'idx_device_owner');
            $table->index(['venue_owner_id', 'status'], 'idx_venue_owner');
            $table->index('status');
            $table->index(['period_start', 'period_end'], 'idx_period');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('settlements');
    }
};
