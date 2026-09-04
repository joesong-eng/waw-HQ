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
        Schema::create('notification_inbox', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained('users')->onDelete('cascade');
            $table->string('title', 255);
            $table->text('body');
            $table->string('type', 50); // alert, settlement, security, info, profit_sharing_approval
            $table->string('action_url', 500)->nullable();
            $table->json('action_data')->nullable();
            $table->boolean('is_read')->default(false);
            $table->timestamps();

            // Indexes
            $table->index('user_id');
            $table->index('is_read');
            $table->index('created_at');
            $table->index(['user_id', 'is_read']);
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('notification_inbox');
    }
};
