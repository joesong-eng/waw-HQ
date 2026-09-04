<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
use Illuminate\Support\Facades\DB;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        DB::statement("ALTER TABLE users MODIFY COLUMN role ENUM('admin', 'owner', 'staff', 'sub_agent') DEFAULT 'owner'");
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        // Reverting this requires dropping sub_agent records or changing their role first.
        // We will just change the schema back, but note it might fail if there are 'sub_agent' records.
        DB::statement("ALTER TABLE users MODIFY COLUMN role ENUM('admin', 'owner', 'staff') DEFAULT 'owner'");
    }
};
