<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    public function up(): void
    {
        Schema::create('device_snapshots', function (Blueprint $row) {
            $row->id();
            $row->string('chip_id')->index();
            $row->unsignedBigInteger('lifetime_credit_in')->default(0);
            $row->unsignedBigInteger('lifetime_credit_out')->default(0);
            $row->timestamp('snapshot_at')->index();
            $row->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('device_snapshots');
    }
};
