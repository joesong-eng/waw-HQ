<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('venue_staff_assignments', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('venue_id');
            $table->unsignedBigInteger('staff_id');
            $table->enum('role', ['manager', 'operator']);
            $table->timestamps();

            // Foreign keys
            $table->foreign('venue_id')->references('id')->on('venues')->onDelete('cascade');
            $table->foreign('staff_id')->references('id')->on('users')->onDelete('cascade');

            // Unique constraint
            $table->unique(['venue_id', 'staff_id']);

            // Indexes
            $table->index('venue_id');
            $table->index('staff_id');
            $table->index('role');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('venue_staff_assignments');
    }
};
