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
        Schema::create('owner_subscriptions', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('owner_id');
            $table->enum('plan_tier', ['basic', 'pro', 'enterprise'])->default('basic');
            $table->date('start_date');
            $table->date('end_date');
            $table->enum('status', ['active', 'expired', 'suspended'])->default('active');
            $table->string('last_payment_ref', 50)->nullable();
            $table->timestamps();
            
            // Indexes
            $table->unique('owner_id');
            $table->index('end_date');
            $table->index('status');
            
            // Foreign key
            $table->foreign('owner_id')
                  ->references('id')
                  ->on('users')
                  ->onDelete('cascade');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('owner_subscriptions');
    }
};
