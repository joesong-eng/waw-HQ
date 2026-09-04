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
        Schema::create('notification_logs', function (Blueprint $table) {
            $table->id();
            $table->string('provider', 20); // line, telegram, system
            $table->string('provider_msg_id', 255)->nullable();
            $table->foreignId('user_id')->constrained('users')->onDelete('cascade');
            $table->foreignId('notification_id')->nullable()->constrained('notification_inbox')->onDelete('set null');
            $table->string('status', 20); // sent, failed
            $table->text('error_msg')->nullable();
            $table->timestamp('sent_at');

            // Indexes
            $table->index('user_id');
            $table->index('notification_id');
            $table->index('provider');
            $table->index('status');
            $table->index('sent_at');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('notification_logs');
    }
};
