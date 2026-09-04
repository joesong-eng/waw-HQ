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
        Schema::create('settlement_logs', function (Blueprint $table) {
            $table->id();
            $table->foreignId('settlement_id')->constrained('settlements')->onDelete('cascade');
            $table->foreignId('user_id')->constrained('users')->onDelete('restrict');
            $table->enum('action', ['created', 'confirmed', 'paid', 'closed', 'disputed', 'resolved']);
            $table->string('from_status', 20)->nullable();
            $table->string('to_status', 20);
            $table->json('metadata')->nullable()->comment('元數據（原因、備註等）');
            $table->string('ip_address', 45)->nullable();
            $table->text('user_agent')->nullable();
            $table->timestamp('created_at')->useCurrent();

            // Indexes
            $table->index(['settlement_id', 'created_at'], 'idx_settlement');
            $table->index(['user_id', 'created_at'], 'idx_user');
            $table->index(['action', 'created_at'], 'idx_action');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('settlement_logs');
    }
};
