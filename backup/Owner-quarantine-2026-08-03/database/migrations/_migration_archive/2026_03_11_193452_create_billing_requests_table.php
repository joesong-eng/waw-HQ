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
        Schema::create('billing_requests', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('owner_id');
            $table->enum('plan_tier', ['pro', 'enterprise']);
            $table->unsignedTinyInteger('duration_months');
            $table->decimal('amount', 10, 2);
            $table->string('payment_ref', 50);
            $table->string('proof_img', 255)->nullable();
            $table->enum('status', ['pending', 'approved', 'rejected', 'cancelled'])->default('pending');
            $table->unsignedBigInteger('reviewed_by')->nullable();
            $table->timestamp('reviewed_at')->nullable();
            $table->text('reject_reason')->nullable();
            $table->timestamp('cancelled_at')->nullable();
            $table->timestamps();
            
            // Indexes
            $table->index(['owner_id', 'status']);
            $table->index('status');
            $table->index('created_at');
            
            // Foreign keys
            $table->foreign('owner_id')
                  ->references('id')
                  ->on('users')
                  ->onDelete('cascade');
            
            $table->foreign('reviewed_by')
                  ->references('id')
                  ->on('users')
                  ->onDelete('set null');
        });
        
        // Add check constraints using raw SQL
        DB::statement('ALTER TABLE billing_requests ADD CONSTRAINT chk_duration CHECK (duration_months >= 1 AND duration_months <= 36)');
        DB::statement('ALTER TABLE billing_requests ADD CONSTRAINT chk_amount CHECK (amount > 0)');
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('billing_requests');
    }
};
